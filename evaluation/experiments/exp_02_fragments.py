"""EXP-02 — Impact du nombre de fragments {1, 2, 3}.

Fait varier le nombre de plateformes fédérées (1 → 2 → 3) sur les **mêmes**
données prétraitées et mesure la qualité du profil. Objectif : valider H2 —
la qualité croît avec le nombre de sources fédérées.
"""

from __future__ import annotations

from typing import Any, Sequence

from evaluation.baselines import FederatedConfig
from evaluation.metrics.profile_metrics import precision_at_k
from evaluation.metrics.reco_metrics import ndcg_at_k
from evaluation.mlflow_tracker import MLflowTracker


class Exp02Fragments:
    """Runner de l'expérience EXP-02."""

    FRAGMENT_COUNTS = (1, 2, 3)

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

    def run(self) -> dict[int, dict[str, float]]:
        """Boucle sur {1, 2, 3} fragments et journalise les métriques."""
        platforms = list(self.platform_texts.keys())
        results: dict[int, dict[str, float]] = {}
        with self.tracker.run("EXP-02-fragments"):
            for n in self.FRAGMENT_COUNTS:
                if n > len(platforms):
                    continue
                subset = {p: self.platform_texts[p] for p in platforms[:n]}
                profile = FederatedConfig().run_pipeline(subset, self.user_hash)
                metrics = self._metrics(profile)
                self.tracker.log_params({"n_fragments": n})
                self.tracker.log_metrics(metrics)
                results[n] = metrics
        return results

    def _metrics(self, profile: dict) -> dict[str, float]:
        interests = profile.get("interests", [])
        return {
            "precision_at_5": precision_at_k(interests, self.holdout, k=5),
            "ndcg_at_10": ndcg_at_k(interests, self.holdout, k=10),
        }
