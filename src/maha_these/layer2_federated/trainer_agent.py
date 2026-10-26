"""TrainerAgent — entraînement LoRA local sur un fragment.

Charge le modèle de base (QLoRA 4-bit), applique LoRA, s'initialise
éventuellement avec les poids globaux (θ_global), entraîne via SFTTrainer,
puis exporte UNIQUEMENT les poids LoRA (Δθ) dans un ``TrainerOutput``.

Dépendances lourdes (transformers, peft, trl, torch) importées paresseusement
pour que le reste du package s'importe sans la pile IA installée.
"""

from __future__ import annotations

import time
from typing import Any

from maha_these.core.base_agent import BaseAgent
from maha_these.core.data_models import TrainerOutput
from .lora_config import DEFAULT_LORA_CFG, LoRAConfigurator


class TrainerAgent(BaseAgent):
    """Agent d'entraînement local d'un fragment fédéré."""

    def __init__(
        self,
        fragment_id: str,
        system_prompt: str,
        lora_cfg: dict[str, Any] | None = None,
        base_model_name: str = "mistralai/Mistral-7B-Instruct-v0.3",
        training_cfg: dict[str, Any] | None = None,
    ) -> None:
        self.fragment_id = fragment_id
        self.name = f"trainer_{fragment_id}"
        self.system_prompt = system_prompt
        self.lora_cfg = lora_cfg or dict(DEFAULT_LORA_CFG)
        self.base_model_name = base_model_name
        self.training_cfg = training_cfg or {}

    def _load_model(self, global_weights: dict | None = None):
        import torch  # imports paresseux
        from peft import get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, BitsAndBytesConfig

        # QLoRA : quantification 4-bit NF4 + double-quant (mémoire réduite,
        # adapté aux petits GPU type 8 Go). Calcul en fp16.
        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            quantization_config=bnb,
            device_map="auto",
        )
        model.config.use_cache = False  # requis avec gradient checkpointing
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
        model = get_peft_model(model, LoRAConfigurator(self.lora_cfg).build())
        if global_weights:  # initialiser avec les poids globaux (θ_global)
            model.load_state_dict(global_weights, strict=False)
        return model

    def run(self, local_dataset, global_weights: dict | None = None) -> TrainerOutput:
        """Entraîne LoRA localement et renvoie Δθ (poids LoRA seuls)."""
        from peft import get_peft_model_state_dict
        from transformers import AutoTokenizer
        from trl import SFTConfig, SFTTrainer

        tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"  # évite les débordements en fp16

        model = self._load_model(global_weights)
        start = time.time()

        tcfg = self.training_cfg
        system_prompt = self.system_prompt

        def formatting_func(batch):
            # batch["text"] est une liste de chaînes (map batché de trl)
            return [f"[INST] {system_prompt} [/INST] {t} " for t in batch["text"]]

        sft = SFTConfig(
            output_dir=f"./tmp/{self.fragment_id}",
            num_train_epochs=tcfg.get("num_train_epochs", 1),
            per_device_train_batch_size=tcfg.get("per_device_train_batch_size", 1),
            gradient_accumulation_steps=tcfg.get("gradient_accumulation_steps", 8),
            learning_rate=tcfg.get("learning_rate", 2e-4),
            fp16=tcfg.get("fp16", True),
            gradient_checkpointing=tcfg.get("gradient_checkpointing", True),
            gradient_checkpointing_kwargs={"use_reentrant": False},
            max_seq_length=tcfg.get("max_seq_length", 256),
            seed=tcfg.get("seed", 42),
            lr_scheduler_type=tcfg.get("lr_scheduler_type", "cosine"),
            warmup_ratio=tcfg.get("warmup_ratio", 0.1),
            logging_steps=5,
            save_strategy="no",
            report_to=[],
        )
        trainer = SFTTrainer(
            model=model,
            args=sft,
            train_dataset=local_dataset,
            tokenizer=tokenizer,
            formatting_func=formatting_func,
        )
        trainer.train()

        log = trainer.state.log_history[-1] if trainer.state.log_history else {}
        # Δθ ramenés sur CPU pour que l'agrégation ne retienne pas la VRAM.
        weights = {
            k: v.detach().cpu() for k, v in get_peft_model_state_dict(model).items()
        }
        output = TrainerOutput(
            agent_id=self.fragment_id,
            lora_weights=weights,  # Δθ UNIQUEMENT
            dataset_size=len(local_dataset),
            training_loss=float(log.get("train_loss", 0.0)),
            training_duration_sec=time.time() - start,
        )
        # Libère le modèle + le cache CUDA : indispensable pour enchaîner
        # plusieurs entraînements sur un petit GPU (8 Go) sans OOM. On supprime
        # les références LOCALES puis on vide le cache pour rendre la VRAM.
        import gc

        import torch

        del trainer, model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return output
