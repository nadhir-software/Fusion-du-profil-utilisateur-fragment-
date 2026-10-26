"""CatalogService — catalogue Amazon MULTI-CATÉGORIES, chargé/encodé une fois.

Fusionne plusieurs catégories du dataset McAuley (Amazon Reviews 2023) en un
seul catalogue **riche et diversifié** : chaque persona trouve des items
pertinents dans son domaine. Le catalogue est chargé et encodé une seule fois
(cache mémoire) ; les requêtes de reco réutilisent ce cache.

Catégories configurables via l'environnement :
    AMAZON_CATALOG_CATEGORY = "Cat1,Cat2,Cat3"   (séparées par des virgules)
    AMAZON_CATALOG_LIMIT    = 1500               (items max PAR catégorie)

Le catalogue est de la donnée produits publique (pas des données utilisateurs) :
sa mise en cache disque via HuggingFace est conforme au principe RAM-only.
"""

from __future__ import annotations

import os
from collections import Counter
from functools import lru_cache
from typing import Any

# Défaut : cross-domaine (magazines, tous sujets) + santé/fitness + musique.
# Ajouter Video_Games / Software pour des produits tech/gaming (plus lourds).
DEFAULT_CATEGORIES = [
    "Magazine_Subscriptions",
    "Health_and_Personal_Care",
    "Digital_Music",
]


class CatalogService:
    """Recommande depuis un catalogue Amazon multi-catégories mis en cache."""

    def __init__(
        self, categories: list[str] | None = None, limit_per_category: int = 1500
    ):
        self.categories = categories or list(DEFAULT_CATEGORIES)
        self.limit_per_category = limit_per_category
        self._catalog: list[dict] | None = None
        self._embeddings = None
        self._encoder = None

    def _ensure_loaded(self) -> None:
        if self._catalog is not None:
            return
        from maha_these.data_ingestion.amazon_reviews import (
            download_category,
            load_catalog,
        )
        from maha_these.layer4_recommendation.profile_encoder import ProfileEncoder

        catalog: list[dict] = []
        for category in self.categories:
            path = download_category(category)
            items = load_catalog(path, limit=self.limit_per_category)
            for item in items:
                item["source_category"] = category
            catalog.extend(items)

        self._catalog = catalog
        self._encoder = ProfileEncoder()
        self._embeddings = self._encoder.encode(
            [f"{c['name']} {c['description']}" for c in catalog]
        )

    def info(self) -> dict[str, Any]:
        self._ensure_loaded()
        assert self._catalog is not None
        by_cat = Counter(c.get("source_category") for c in self._catalog)
        return {
            "categories": self.categories,
            "size": len(self._catalog),
            "by_category": dict(by_cat),
        }

    def recommend(self, profile: dict, top_k: int = 10) -> list[dict[str, Any]]:
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        self._ensure_loaded()
        assert self._catalog is not None and self._encoder is not None
        prof_emb = self._encoder.encode_profiles([profile])
        sims = cosine_similarity(prof_emb, self._embeddings)[0]
        top = np.argsort(sims)[::-1][:top_k]
        return [
            {
                "item_id": self._catalog[j]["id"],
                "item_name": self._catalog[j]["name"],
                "category": self._catalog[j].get("source_category")
                or self._catalog[j]["category"],
                "relevance_score": round(float(sims[j]), 4),
                "rank": rank + 1,
            }
            for rank, j in enumerate(top)
        ]


@lru_cache(maxsize=1)
def get_catalog_service() -> CatalogService:
    """Singleton — catégories & limite lues depuis l'environnement."""
    env = os.getenv("AMAZON_CATALOG_CATEGORY", "")
    categories = [c.strip() for c in env.split(",") if c.strip()] or None
    limit = int(os.getenv("AMAZON_CATALOG_LIMIT", "1500"))
    return CatalogService(categories, limit_per_category=limit)
