"""Métriques de confidentialité : volume des Δθ, ratio privacy/utility."""

from __future__ import annotations

from typing import Any


def delta_theta_volume(lora_weights: dict[str, Any]) -> int:
    """Nombre total de paramètres transmis (taille des Δθ échangés).

    Sert à quantifier le coût de communication et l'exposition : plus le
    volume est faible, plus l'échange fédéré est léger et privé.
    """
    total = 0
    for tensor in lora_weights.values():
        numel = getattr(tensor, "numel", None)
        total += numel() if callable(numel) else len(tensor)
    return total


def privacy_utility_ratio(utility_score: float, privacy_cost: float) -> float:
    """Ratio utilité/coût de confidentialité (plus haut = meilleur compromis).

    Args:
        utility_score: métrique de qualité (ex : cohérence sémantique).
        privacy_cost:  coût de confidentialité (ex : sigma DP, volume Δθ normalisé).
    """
    if privacy_cost <= 0:
        return float("inf")
    return utility_score / privacy_cost
