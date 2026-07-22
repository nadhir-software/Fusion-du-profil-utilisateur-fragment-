"""EXP-03 — Qualité de recommandation : fédéré vs centralisé.

Compare NDCG@K / Précision@K / Davies-Bouldin des recommandations issues des
profils fédérés versus centralisés.
"""

from __future__ import annotations

from typing import Any

from evaluation.mlflow_tracker import MLflowTracker


class Exp03Recommendation:
    """Runner de l'expérience EXP-03."""

    TOP_K = (5, 10, 20)

    def __init__(self, data: Any, tracker: MLflowTracker | None = None) -> None:
        self.data = data
        self.tracker = tracker or MLflowTracker()

    def run(self) -> dict[str, dict[str, float]]:
        # TODO(Phase 3): générer les recos par config et mesurer la qualité.
        raise NotImplementedError("EXP-03 à brancher (Phase 3).")
