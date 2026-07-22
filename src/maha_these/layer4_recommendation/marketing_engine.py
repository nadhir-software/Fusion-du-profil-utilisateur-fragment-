"""MarketingRecommender — orchestration des deux axes de recommandation.

Axe 1 (utilisateur)  : recommend_to_user(profil, catalogue) -> items.
Axe 2 (marketeur)    : find_target_segments(campagne, profils) -> segments.

Point d'entrée unique utilisé par la couche API (layer5).
"""

from __future__ import annotations

from typing import Any

from .content_based import ContentBasedRecommender
from .profile_encoder import ProfileEncoder
from .segment_clustering import SegmentClustering


class MarketingRecommender:
    """Façade orchestrant les recommandeurs des deux axes."""

    def __init__(self, model_name: str = "all-mpnet-base-v2") -> None:
        self.encoder = ProfileEncoder(model_name)
        self.content_based = ContentBasedRecommender(model_name)
        self.clustering = SegmentClustering(self.encoder)

    def recommend_to_user(
        self, profile: dict[str, Any], catalog: list[dict[str, Any]], top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Axe 1 : recommandations personnalisées pour un utilisateur."""
        return self.content_based.recommend(profile, catalog, top_k=top_k)

    def find_target_segments(
        self,
        campaign: dict[str, Any],
        profiles: list[dict[str, Any]],
        threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Axe 2 : segments de profils cibles pour une campagne."""
        return self.clustering.find_target_segments(
            campaign, profiles, threshold=threshold
        )
