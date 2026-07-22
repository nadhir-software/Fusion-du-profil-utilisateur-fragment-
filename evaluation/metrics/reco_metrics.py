"""Métriques de recommandation : NDCG@K, Précision@K, Davies-Bouldin."""

from __future__ import annotations

import math
from typing import Any, Sequence

from .profile_metrics import precision_at_k  # réutilisation

__all__ = ["precision_at_k", "ndcg_at_k", "davies_bouldin"]


def _dcg(gains: Sequence[float]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(predicted: Sequence[Any], relevant: Sequence[Any], k: int) -> float:
    """NDCG@K avec gains binaires (1 si pertinent, 0 sinon)."""
    if k <= 0:
        return 0.0
    relevant_set = set(relevant)
    gains = [1.0 if item in relevant_set else 0.0 for item in list(predicted)[:k]]
    dcg = _dcg(gains)
    ideal_gains = sorted(gains, reverse=True)
    idcg = _dcg(ideal_gains)
    return dcg / idcg if idcg > 0 else 0.0


def davies_bouldin(embeddings, labels) -> float:
    """Indice de Davies-Bouldin (qualité des segments ; plus bas = mieux)."""
    from sklearn.metrics import davies_bouldin_score  # import paresseux

    return float(davies_bouldin_score(embeddings, labels))
