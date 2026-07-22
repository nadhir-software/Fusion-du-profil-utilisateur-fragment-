"""ContentBasedRecommender — recommandation par similarité cosinus.

Axe 1 (utilisateur) : encode le profil et le catalogue, calcule la similarité
cosinus profil ↔ items, renvoie le top-K trié par pertinence.
"""

from __future__ import annotations

from typing import Any

from .profile_encoder import ProfileEncoder


class ContentBasedRecommender:
    """Recommandeur content-based (Sentence-BERT + cosine similarity)."""

    def __init__(self, model_name: str = "all-mpnet-base-v2") -> None:
        self.encoder = ProfileEncoder(model_name)

    def recommend(
        self, profile: dict[str, Any], catalog: list[dict[str, Any]], top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Renvoie les ``top_k`` items les plus pertinents pour le profil."""
        from sklearn.metrics.pairwise import cosine_similarity  # import paresseux
        import numpy as np

        if not catalog:
            return []

        profile_text = ProfileEncoder.profile_to_text(profile)
        profile_emb = self.encoder.encode([profile_text])
        item_texts = [
            f"{i.get('name', '')} {i.get('description', '')} {i.get('category', '')}"
            for i in catalog
        ]
        item_embs = self.encoder.encode(item_texts)

        scores = cosine_similarity(profile_emb, item_embs)[0]
        top_idx = np.argsort(scores)[-top_k:][::-1]
        return [
            {
                "item_id": catalog[i].get("id"),
                "item_name": catalog[i].get("name"),
                "category": catalog[i].get("category"),
                "relevance_score": round(float(scores[i]), 4),
                "rank": rank + 1,
            }
            for rank, i in enumerate(top_idx)
        ]
