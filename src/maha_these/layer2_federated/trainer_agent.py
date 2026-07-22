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
        from peft import get_peft_model  # imports paresseux
        from transformers import AutoModelForCausalLM

        model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            load_in_4bit=True,  # QLoRA
            device_map="auto",
        )
        model = get_peft_model(model, LoRAConfigurator(self.lora_cfg).build())
        if global_weights:  # initialiser avec les poids globaux
            model.load_state_dict(global_weights, strict=False)
        return model

    def run(self, local_dataset, global_weights: dict | None = None) -> TrainerOutput:
        """Entraîne LoRA localement et renvoie Δθ (poids LoRA seuls)."""
        from peft import get_peft_model_state_dict
        from transformers import TrainingArguments
        from trl import SFTTrainer

        model = self._load_model(global_weights)
        start = time.time()

        tcfg = self.training_cfg
        trainer = SFTTrainer(
            model=model,
            train_dataset=local_dataset,
            formatting_func=lambda x: [
                f"[INST] {self.system_prompt} [/INST] {x['text']} "
            ],
            args=TrainingArguments(
                output_dir=f"./tmp/{self.fragment_id}",
                num_train_epochs=tcfg.get("num_train_epochs", 3),
                per_device_train_batch_size=tcfg.get("per_device_train_batch_size", 4),
                gradient_accumulation_steps=tcfg.get("gradient_accumulation_steps", 4),
                learning_rate=tcfg.get("learning_rate", 2e-4),
                fp16=tcfg.get("fp16", True),
                gradient_checkpointing=tcfg.get("gradient_checkpointing", True),
                seed=tcfg.get("seed", 42),
                lr_scheduler_type=tcfg.get("lr_scheduler_type", "cosine"),
                warmup_ratio=tcfg.get("warmup_ratio", 0.1),
                logging_steps=10,
                save_steps=0,
            ),
        )
        trainer.train()

        log = trainer.state.log_history[-1] if trainer.state.log_history else {}
        return TrainerOutput(
            agent_id=self.fragment_id,
            lora_weights=get_peft_model_state_dict(model),  # Δθ UNIQUEMENT
            dataset_size=len(local_dataset),
            training_loss=float(log.get("train_loss", 0.0)),
            training_duration_sec=time.time() - start,
        )
