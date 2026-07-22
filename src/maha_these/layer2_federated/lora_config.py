"""LoRAConfigurator — construction de la configuration PEFT/LoRA.

Centralise les hyperparamètres LoRA (r, alpha, dropout, target_modules) et
produit un ``peft.LoraConfig``. La valeur par défaut suit le plan : r=16,
alpha=32, cibles q/v/k/o_proj.
"""

from __future__ import annotations

from typing import Any

DEFAULT_LORA_CFG: dict[str, Any] = {
    "r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
    "bias": "none",
}


class LoRAConfigurator:
    """Fabrique de ``peft.LoraConfig`` à partir d'un dict d'hyperparamètres."""

    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        self.cfg = {**DEFAULT_LORA_CFG, **(cfg or {})}

    def build(self):
        """Renvoie un ``peft.LoraConfig`` (import paresseux de peft)."""
        try:
            from peft import LoraConfig, TaskType  # import paresseux
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "La librairie `peft` est requise pour LoRAConfigurator. "
                "Installez la pile IA : pip install -r requirements-ai.txt"
            ) from exc

        return LoraConfig(
            r=self.cfg["r"],
            lora_alpha=self.cfg["lora_alpha"],
            lora_dropout=self.cfg["lora_dropout"],
            target_modules=self.cfg["target_modules"],
            bias=self.cfg["bias"],
            task_type=TaskType.CAUSAL_LM,
        )
