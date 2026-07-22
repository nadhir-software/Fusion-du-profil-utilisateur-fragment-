"""WeightsExporter — extraction et persistance des poids LoRA (Δθ).

Fournit un point unique pour :
- extraire les Δθ d'un modèle PEFT (``get_peft_model_state_dict``) ;
- sauvegarder/recharger les Δθ sur disque.

Garantie de confidentialité : on n'exporte QUE des tenseurs de poids LoRA,
jamais de données d'entraînement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class WeightsExporter:
    """Export/import des deltas de poids LoRA."""

    @staticmethod
    def extract(model) -> dict[str, Any]:
        """Extrait les Δθ (poids LoRA) d'un modèle PEFT."""
        from peft import get_peft_model_state_dict  # import paresseux

        return get_peft_model_state_dict(model)

    @staticmethod
    def save(weights: dict[str, Any], path: str | Path) -> Path:
        """Sérialise les Δθ sur disque (format torch)."""
        import torch  # import paresseux

        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        torch.save(weights, out)
        return out

    @staticmethod
    def load(path: str | Path) -> dict[str, Any]:
        """Recharge les Δθ depuis le disque."""
        import torch  # import paresseux

        return torch.load(Path(path), map_location="cpu")
