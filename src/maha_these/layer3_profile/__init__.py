"""Couche 3 — Agrégation fédérée & profil global unifié.

FedAvg/FedProx sur les Δθ, génération du profil par inférence LLM,
puis stockage/indexation des profils JSON.
"""

from .aggregator import FederatedAggregator
from .profile_generator import ProfileGenerator
from .profile_store import ProfileStore

__all__ = ["FederatedAggregator", "ProfileGenerator", "ProfileStore"]
