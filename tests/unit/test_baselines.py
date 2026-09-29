"""Tests baselines EXP-01 — plans de fragmentation (purs) + harnais mocké."""

import contextlib

from evaluation.baselines import (
    CentralizedConfig,
    FederatedConfig,
    MonoSourceConfig,
)
from evaluation.experiments.exp_01_comparison import Exp01Comparison

PLATFORM_TEXTS = {
    "reddit": ["a b c d e", "f g h i j"],
    "linkedin": ["k l m n o"],
    "amazon": ["p q r s t"],
}


def test_federated_plan_one_fragment_per_platform():
    plan = FederatedConfig().fragment_plan(PLATFORM_TEXTS)
    assert set(plan.keys()) == {"F1_reddit", "F2_linkedin", "F3_amazon"}
    assert plan["F1_reddit"] == ["a b c d e", "f g h i j"]


def test_centralized_plan_merges_everything():
    plan = CentralizedConfig().fragment_plan(PLATFORM_TEXTS)
    assert list(plan.keys()) == ["F_central"]
    assert len(plan["F_central"]) == 4  # 2 + 1 + 1


def test_mono_source_plan_reddit_only():
    plan = MonoSourceConfig().fragment_plan(PLATFORM_TEXTS)
    assert list(plan.keys()) == ["F1_reddit"]
    assert plan["F1_reddit"] == ["a b c d e", "f g h i j"]


class _FakeTracker:
    """Tracker no-op (évite la dépendance MLflow dans les tests)."""

    def run(self, name):
        return contextlib.nullcontext()

    def log_params(self, params):
        pass

    def log_metrics(self, metrics):
        pass


def test_exp01_harness_computes_metrics_for_three_configs(monkeypatch):
    # Profil factice par config -> métriques calculées sans pile ML.
    def fake_run(self, platform_texts, user_hash="exp_user"):
        return {"user_hash": user_hash, "interests": ["python", "ml", "cyclisme"]}

    monkeypatch.setattr(
        "evaluation.baselines.BaselineConfig.run_pipeline", fake_run, raising=True
    )

    exp = Exp01Comparison(
        PLATFORM_TEXTS, holdout=["python", "ml"], tracker=_FakeTracker()
    )
    results = exp.run()

    assert set(results.keys()) == {"federated", "centralized", "mono_source"}
    # top-1 = "python" ∈ holdout -> precision@1 = 1.0 ; ndcg@10 parfait
    assert results["federated"]["precision_at_1"] == 1.0
    assert results["federated"]["ndcg_at_10"] == 1.0
