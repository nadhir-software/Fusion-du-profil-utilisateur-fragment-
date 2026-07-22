"""SegmentClustering — identification de segments marketing (Axe marketeur).

Filtre les profils dont l'affinité avec une campagne dépasse un seuil, puis
les regroupe par KMeans en segments homogènes triés par affinité moyenne.
"""

from __future__ import annotations

from typing import Any

from .profile_encoder import ProfileEncoder


class SegmentClustering:
    """Clustering de profils cibles pour une campagne."""

    def __init__(self, encoder: ProfileEncoder | None = None) -> None:
        self.encoder = encoder or ProfileEncoder()

    def find_target_segments(
        self,
        campaign: dict[str, Any],
        profiles: list[dict[str, Any]],
        threshold: float = 0.5,
        max_clusters: int = 5,
    ) -> list[dict[str, Any]]:
        """Renvoie les segments cibles pour une campagne, triés par affinité."""
        from sklearn.cluster import KMeans  # imports paresseux
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        if not profiles:
            return []

        campaign_emb = self.encoder.encode([campaign["description"]])
        profile_embs = self.encoder.encode_profiles(profiles)
        scores = cosine_similarity(campaign_emb, profile_embs)[0]

        # Filtrer les profils au-dessus du seuil d'affinité.
        target_mask = scores > threshold
        target_profiles = [p for p, m in zip(profiles, target_mask) if m]
        target_embs = profile_embs[target_mask]

        n_clusters = min(max_clusters, len(target_profiles))
        if n_clusters < 2:
            return []

        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(target_embs)
        target_scores = scores[target_mask]

        segments: list[dict[str, Any]] = []
        for seg_id in range(n_clusters):
            members = [p for p, l in zip(target_profiles, labels) if l == seg_id]
            avg = float(np.mean(target_scores[labels == seg_id]))
            segments.append(
                {
                    "segment_id": f"SEG_{seg_id + 1}",
                    "size": len(members),
                    "avg_affinity": round(avg, 4),
                    "profile_hashes": [p["user_hash"] for p in members],
                }
            )
        return sorted(segments, key=lambda s: s["avg_affinity"], reverse=True)
