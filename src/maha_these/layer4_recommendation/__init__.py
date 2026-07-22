"""Couche 4 — Moteur de recommandation marketing (pipeline dual).

Axe 1 (utilisateur) : profil → items pertinents (content-based + LLM).
Axe 2 (marketeur)   : campagne → segments de profils cibles (clustering).
"""

from .content_based import ContentBasedRecommender
from .marketing_engine import MarketingRecommender
from .profile_encoder import ProfileEncoder
from .segment_clustering import SegmentClustering

__all__ = [
    "ProfileEncoder",
    "ContentBasedRecommender",
    "SegmentClustering",
    "MarketingRecommender",
]
