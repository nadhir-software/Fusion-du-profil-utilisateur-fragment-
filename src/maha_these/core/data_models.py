"""Modèles de données Pydantic partagés par tout le pipeline.

Post / Comment      : unités collectées par les crawlers (Couche 1).
Fragment            : jeu de données local prêt à l'entraînement (Couche 2).
TrainerOutput       : sortie d'un TrainerAgent — SEULEMENT des poids LoRA (Δθ).
UserProfile         : profil global unifié généré après agrégation (Couche 3).

Invariant de confidentialité : aucun de ces modèles ne transporte
d'identifiant nominatif ; seul ``user_hash`` (SHA-256) est utilisé.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

SignalType = Literal["interest", "professional", "purchase"]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Post(BaseModel):
    """Un post public collecté sur une plateforme."""

    id: str
    title: str = ""
    body: str = ""
    subreddit: str = ""
    score: int = 0
    created_utc: float = 0.0
    type: Literal["post"] = "post"


class Comment(BaseModel):
    """Un commentaire public collecté sur une plateforme."""

    id: str
    body: str = ""
    subreddit: str = ""
    score: int = 0
    created_utc: float = 0.0
    type: Literal["comment"] = "comment"


class Fragment(BaseModel):
    """Fragment fédéré : données locales d'une plateforme, prêtes à entraîner."""

    fragment_id: str  # ex: "F1_reddit"
    signal_type: SignalType
    user_hash: str
    n_samples: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrainerOutput(BaseModel):
    """Sortie d'un TrainerAgent.

    ``lora_weights`` contient UNIQUEMENT les poids LoRA (Δθ) — JAMAIS les
    données brutes ni le texte. Voir tests/unit/test_lora_export.py.
    """

    agent_id: str
    # dict[str, torch.Tensor] au runtime ; typé Any pour éviter une dépendance
    # dure à torch dans les modèles de données.
    lora_weights: dict[str, Any]
    dataset_size: int
    training_loss: float = 0.0
    training_duration_sec: float = 0.0

    model_config = {"arbitrary_types_allowed": True}


class UserProfile(BaseModel):
    """Profil global unifié d'un utilisateur (Couche 3)."""

    user_hash: str
    interests: list[str] = Field(default_factory=list)
    needs: dict[str, Any] = Field(default_factory=dict)
    professional: dict[str, Any] = Field(default_factory=dict)
    consumption: dict[str, Any] = Field(default_factory=dict)
    marketing_segments: list[str] = Field(default_factory=list)
    platforms_covered: list[str] = Field(default_factory=list)
    profile_version: str = "federated"
    generated_at: str = Field(default_factory=_utcnow_iso)
    error: Optional[str] = None
