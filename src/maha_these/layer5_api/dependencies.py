"""Injection de dépendances FastAPI.

Fournit des singletons légers (magasin de profils, moteur de recommandation)
réutilisés par les routeurs. Les objets lourds sont instanciés paresseusement.
"""

from __future__ import annotations

import uuid
from functools import lru_cache

from maha_these.layer3_profile.profile_store import ProfileStore


def generate_job_id() -> str:
    """Identifiant de job pour les traitements asynchrones (crawl/train)."""
    return uuid.uuid4().hex


def get_profile_store() -> type[ProfileStore]:
    """Dépendance : magasin de profils."""
    return ProfileStore


@lru_cache(maxsize=1)
def get_recommender():
    """Dépendance : moteur de recommandation (chargé une seule fois).

    Import paresseux : évite de charger Sentence-BERT tant qu'aucune route de
    recommandation n'est appelée.
    """
    from maha_these.layer4_recommendation.marketing_engine import (
        MarketingRecommender,
    )

    return MarketingRecommender()
