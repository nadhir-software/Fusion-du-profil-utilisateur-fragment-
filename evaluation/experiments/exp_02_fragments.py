"""EXP-02 — Impact du nombre de fragments {1, 2, 3}.

Objectif : valider H2 (la qualité du profil croît avec le nombre de sources
fédérées). Fait varier le nombre de fragments et mesure cohérence + ROUGE-L.
"""

from __future__ import annotations

from typing import Any

from evaluation.mlflow_tracker import MLflowTracker


class Exp02Fragments:
    """Runner de l'expérience EXP-02."""

    FRAGMENT_COUNTS = (1, 2, 3)

    def __init__(self, data: Any, tracker: MLflowTracker | None = None) -> None:
        self.data = data
        self.tracker = tracker or MLflowTracker()

    def run(self) -> dict[int, dict[str, float]]:
        """Boucle sur {1, 2, 3} fragments et journalise les métriques."""
        # TODO(Phase 3): entraîner avec n fragments et mesurer la qualité.
        raise NotImplementedError("EXP-02 à brancher (Phase 3).")
