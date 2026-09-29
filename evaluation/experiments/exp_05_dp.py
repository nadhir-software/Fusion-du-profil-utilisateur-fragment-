"""EXP-05 — Differential Privacy (optionnel).

Fait varier l'écart-type du bruit gaussien ``sigma`` ajouté à θ_global avant
génération, et mesure le compromis **privacy / utility** : plus sigma est élevé,
plus la confidentialité augmente mais plus l'utilité (qualité du profil) risque
de baisser. Le bruit DP est appliqué dans ``BaselineConfig._aggregate`` via
``fed_cfg["dp_noise_sigma"]``.
"""

from __future__ import annotations

from typing import Any, Sequence

from evaluation.baselines import FederatedConfig
from evaluation.metrics.privacy_metrics import privacy_utility_ratio
from evaluation.metrics.reco_metrics import ndcg_at_k
from evaluation.mlflow_tracker import MLflowTracker


class Exp05DifferentialPrivacy:
    """Runner de l'expérience optionnelle EXP-05."""

    SIGMAS = (0.0, 0.05, 0.1, 0.2)

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

    def run(self) -> dict[float, dict[str, float]]:
        """Boucle sur les niveaux de bruit DP et mesure le compromis."""
        results: dict[float, dict[str, float]] = {}
        with self.tracker.run("EXP-05-dp"):
            for sigma in self.SIGMAS:
                config = FederatedConfig(
                    fed_cfg={"algorithm": "fedavg", "dp_noise_sigma": sigma}
                )
                profile = config.run_pipeline(self.platform_texts, self.user_hash)
                utility = ndcg_at_k(profile.get("interests", []), self.holdout, k=10)
                ratio = privacy_utility_ratio(utility, sigma) if sigma > 0 else None

                self.tracker.log_params({"dp_sigma": sigma})
                logged = {"utility_ndcg_at_10": utility}
                if ratio is not None:
                    logged["privacy_utility_ratio"] = ratio
                self.tracker.log_metrics(logged)

                results[sigma] = {"utility_ndcg_at_10": utility, "ratio": ratio}
        return results
