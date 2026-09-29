"""EXP-03 — Qualité de recommandation : fédéré vs centralisé.

À partir des profils générés par chaque configuration, exécute le moteur de
recommandation content-based (Sentence-BERT) sur un catalogue et mesure la
qualité du classement (Précision@K, NDCG@K) contre une vérité terrain d'items
pertinents. Le moteur de reco étant installé, cette campagne est **exécutable**
dès que les profils sont fournis.
"""

from __future__ import annotations

from typing import Any, Sequence

from evaluation.metrics.profile_metrics import precision_at_k
from evaluation.metrics.reco_metrics import ndcg_at_k
from evaluation.mlflow_tracker import MLflowTracker
from maha_these.layer4_recommendation.content_based import ContentBasedRecommender


class Exp03Recommendation:
    """Runner de l'expérience EXP-03."""

    TOP_K = (5, 10, 20)

    def __init__(
        self,
        profiles_by_config: dict[str, dict],
        catalog: list[dict],
        relevant_items: Sequence[Any],
        encoder_model: str = "all-mpnet-base-v2",
        tracker: Any | None = None,
    ) -> None:
        self.profiles_by_config = profiles_by_config
        self.catalog = catalog
        self.relevant_items = relevant_items
        self.tracker = tracker or MLflowTracker()
        self.recommender = ContentBasedRecommender(encoder_model)

    def run(self) -> dict[str, dict[str, float]]:
        """Compare la qualité de reco entre configurations."""
        results: dict[str, dict[str, float]] = {}
        with self.tracker.run("EXP-03-recommendation"):
            for config_name, profile in self.profiles_by_config.items():
                metrics: dict[str, float] = {}
                for k in self.TOP_K:
                    predicted = [r["item_id"] for r in self._recommend(profile, k)]
                    metrics[f"precision_at_{k}"] = precision_at_k(
                        predicted, self.relevant_items, k
                    )
                    metrics[f"ndcg_at_{k}"] = ndcg_at_k(
                        predicted, self.relevant_items, k
                    )
                self.tracker.log_params({"config": config_name})
                self.tracker.log_metrics(metrics)
                results[config_name] = metrics
        return results

    def _recommend(self, profile: dict, k: int) -> list[dict]:
        return self.recommender.recommend(profile, self.catalog, top_k=k)
