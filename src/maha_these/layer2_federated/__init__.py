"""Couche 2 — Fragmentation fédérée sécurisée (LLM + LoRA).

Prétraitement local, construction des fragments HuggingFace, puis
entraînement LoRA local par TrainerAgent. Seuls les Δθ (poids LoRA) sortent.
"""

from .fragment_builder import FragmentBuilder
from .lora_config import LoRAConfigurator
from .preprocessor import PreprocessorAgent
from .system_prompts import SYSTEM_PROMPTS
from .trainer_agent import TrainerAgent

__all__ = [
    "PreprocessorAgent",
    "FragmentBuilder",
    "LoRAConfigurator",
    "TrainerAgent",
    "SYSTEM_PROMPTS",
]
