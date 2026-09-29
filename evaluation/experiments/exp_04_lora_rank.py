"""EXP-04 — Ablation du rang LoRA r ∈ {4, 8, 16, 32}.

Fait varier le rang LoRA (avec ``alpha = 2·r``) sur les **mêmes** données et
mesure le compromis qualité/capacité. Objectif : trouver le rang optimal.
"""

from __future__ import annotations

from typing import Any, Sequence

from evaluation.baselines import FederatedConfig
from evaluation.metrics.profile_metrics import precision_at_k
from evaluation.metrics.reco_metrics import ndcg_at_k
from evaluation.mlflow_tracker import MLflowTracker
from maha_these.layer2_federated.lora_config import DEFAULT_LORA_CFG


class Exp04LoraRank:
    """Runner de l'expérience EXP-04."""

    LORA_RANKS = (4, 8, 16, 32)

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
        """Boucle sur les rangs LoRA et journalise les métriques."""
        results: dict[int, dict[str, float]] = {}
        with self.tracker.run("EXP-04-lora-rank"):
            for r in self.LORA_RANKS:
                lora_cfg = {**DEFAULT_LORA_CFG, "r": r, "lora_alpha": 2 * r}
                config = FederatedConfig(lora_cfg=lora_cfg)
                profile = config.run_pipeline(self.platform_texts, self.user_hash)
                metrics = self._metrics(profile)
                self.tracker.log_params({"lora_r": r, "lora_alpha": 2 * r})
                self.tracker.log_metrics(metrics)
                results[r] = metrics
        return results

    def _metrics(self, profile: dict) -> dict[str, float]:
        interests = profile.get("interests", [])
        return {
            "precision_at_5": precision_at_k(interests, self.holdout, k=5),
            "ndcg_at_10": ndcg_at_k(interests, self.holdout, k=10),
        }
