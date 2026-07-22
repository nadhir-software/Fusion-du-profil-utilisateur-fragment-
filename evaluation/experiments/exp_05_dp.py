"""EXP-05 — Differential Privacy (OPTIONNEL).

Étudie le ratio privacy/utility en ajoutant du bruit gaussien (sigma) aux Δθ
avant agrégation. Extension au-delà du périmètre principal de la thèse.
"""

from __future__ import annotations

from typing import Any

from evaluation.mlflow_tracker import MLflowTracker


class Exp05DifferentialPrivacy:
    """Runner de l'expérience optionnelle EXP-05."""

    SIGMAS = (0.0, 0.05, 0.1, 0.2)

    def __init__(self, data: Any, tracker: MLflowTracker | None = None) -> None:
        self.data = data
        self.tracker = tracker or MLflowTracker()

    def run(self) -> dict[float, dict[str, float]]:
        # TODO(optionnel): ajouter DP noise et mesurer le compromis.
        raise NotImplementedError("EXP-05 (DP) optionnel — à brancher.")
