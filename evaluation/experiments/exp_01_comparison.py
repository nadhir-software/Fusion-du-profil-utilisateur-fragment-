"""EXP-01 — Comparaison fédéré vs centralisé vs mono-source.

Objectif : valider H1 (le fédéré atteint une qualité ≈ centralisée) via un
test de Wilcoxon. Journalise les métriques par configuration dans MLflow.
"""

from __future__ import annotations

from typing import Any

from evaluation.baselines import (
    CentralizedConfig,
    FederatedConfig,
    MonoSourceConfig,
)
from evaluation.metrics.profile_metrics import precision_at_k
from evaluation.metrics.reco_metrics import ndcg_at_k
from evaluation.mlflow_tracker import MLflowTracker


class Exp01Comparison:
    """Runner de l'expérience EXP-01."""

    def __init__(self, data: Any, holdout: Any, tracker: MLflowTracker | None = None):
        self.data = data
        self.holdout = holdout
        self.tracker = tracker or MLflowTracker()

    def run(self) -> dict[str, dict[str, float]]:
        """Exécute les trois configs et renvoie leurs métriques."""
        configs = [
            ("federated", FederatedConfig()),
            ("centralized", CentralizedConfig()),
            ("mono_source", MonoSourceConfig()),
        ]
        results: dict[str, dict[str, float]] = {}
        with self.tracker.run("EXP-01-comparison"):
            for name, config in configs:
                profile = config.run_pipeline(
                    self.data
                )  # NotImplemented tant que Phase 3
                metrics = self._evaluate(profile)
                self.tracker.log_params({"config": name})
                self.tracker.log_metrics(metrics)
                results[name] = metrics
        return results

    def _evaluate(self, profile: dict[str, Any]) -> dict[str, float]:
        # TODO(Phase 3): brancher les vraies références (holdout, sources).
        return {
            "precision_at_1": precision_at_k(
                profile.get("interests", []), self.holdout, k=1
            ),
            "precision_at_5": precision_at_k(
                profile.get("interests", []), self.holdout, k=5
            ),
            "ndcg_at_10": ndcg_at_k(profile.get("interests", []), self.holdout, k=10),
        }
