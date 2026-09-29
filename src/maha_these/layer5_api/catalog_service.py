"""CatalogService — catalogue Amazon chargé et encodé une seule fois (cache).

Charge la métadonnée produits Amazon (dataset McAuley) au premier appel, encode
tous les items avec Sentence-BERT et met les embeddings en cache mémoire. Les
requêtes de recommandation réutilisent ce cache (rapide). Le catalogue est de la
**donnée produits publique** (pas des données utilisateurs) : sa mise en cache
disque via HuggingFace est conforme au principe RAM-only, qui vise les données
personnelles.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


class CatalogService:
    """Fournit des recommandations depuis un catalogue Amazon mis en cache."""

    def __init__(self, category: str = "Magazine_Subscriptions", limit: int = 3000):
        self.category = category
        self.limit = limit
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

        path = download_category(self.category)
        self._catalog = load_catalog(path, limit=self.limit)
        self._encoder = ProfileEncoder()
        self._embeddings = self._encoder.encode(
            [f"{c['name']} {c['description']}" for c in self._catalog]
        )

    def info(self) -> dict[str, Any]:
        self._ensure_loaded()
        return {"category": self.category, "size": len(self._catalog or [])}

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
                "category": self._catalog[j]["category"],
                "relevance_score": round(float(sims[j]), 4),
                "rank": rank + 1,
            }
            for rank, j in enumerate(top)
        ]


@lru_cache(maxsize=1)
def get_catalog_service() -> CatalogService:
    """Singleton du service de catalogue (catégorie configurable via env)."""
    return CatalogService(
        category=os.getenv("AMAZON_CATALOG_CATEGORY", "Magazine_Subscriptions"),
        limit=int(os.getenv("AMAZON_CATALOG_LIMIT", "3000")),
    )
