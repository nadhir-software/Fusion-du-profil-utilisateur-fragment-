"""EXP-01 — Comparaison fédéré vs centralisé vs mono-source.

Exécute les trois configurations sur les **mêmes** données prétraitées
(``platform_texts`` = ``{platform: [textes]}``) et le même holdout, calcule les
métriques par configuration, et les journalise dans MLflow. Objectif : valider
H1 (le fédéré atteint une qualité ≈ centralisée).
"""

from __future__ import annotations

from typing import Any, Sequence

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

    def __init__(
        self,
        platform_texts: dict[str, list[str]],
        holdout: Sequence[Any],
        user_hash: str = "exp_user",
        tracker: Any | None = None,
    ) -> None:
        self.platform_texts = platform_texts
        self.holdout = holdout
        self.user_hash = user_hash
        self.tracker = tracker or MLflowTracker()

    def run(self) -> dict[str, dict[str, float]]:
        """Exécute les 3 configs et renvoie leurs métriques."""
        configs = [FederatedConfig(), CentralizedConfig(), MonoSourceConfig()]
        results: dict[str, dict[str, float]] = {}
        with self.tracker.run("EXP-01-comparison"):
            for config in configs:
                profile = config.run_pipeline(self.platform_texts, self.user_hash)
                metrics = self._metrics(profile)
                self.tracker.log_params({"config": config.name})
                self.tracker.log_metrics(metrics)
                results[config.name] = metrics
        return results

    def _metrics(self, profile: dict) -> dict[str, float]:
        interests = profile.get("interests", [])
        return {
            "precision_at_1": precision_at_k(interests, self.holdout, k=1),
            "precision_at_5": precision_at_k(interests, self.holdout, k=5),
            "ndcg_at_10": ndcg_at_k(interests, self.holdout, k=10),
        }
