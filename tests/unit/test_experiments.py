"""Tests EXP-02 (nombre de fragments) & EXP-04 (rang LoRA) — harnais mockés."""

import contextlib

from evaluation.experiments.exp_02_fragments import Exp02Fragments
from evaluation.experiments.exp_04_lora_rank import Exp04LoraRank

PLATFORM_TEXTS = {
    "reddit": ["a b c d e"],
    "linkedin": ["f g h i j"],
    "amazon": ["k l m n o"],
}


class _FakeTracker:
    def run(self, name):
        return contextlib.nullcontext()

    def log_params(self, params):
        pass

    def log_metrics(self, metrics):
        pass


def test_exp02_varies_fragment_count(monkeypatch):
    seen_counts = []

    def fake_run(self, platform_texts, user_hash="exp_user"):
        seen_counts.append(len(platform_texts))
        return {"user_hash": user_hash, "interests": ["python"]}

    monkeypatch.setattr(
        "evaluation.baselines.BaselineConfig.run_pipeline", fake_run, raising=True
    )

    exp = Exp02Fragments(PLATFORM_TEXTS, holdout=["python"], tracker=_FakeTracker())
    results = exp.run()

    assert set(results.keys()) == {1, 2, 3}
    assert seen_counts == [1, 2, 3]  # 1 puis 2 puis 3 plateformes
    assert results[1]["precision_at_5"] == 1.0


def test_exp02_skips_counts_above_available(monkeypatch):
    monkeypatch.setattr(
        "evaluation.baselines.BaselineConfig.run_pipeline",
        lambda self, pt, user_hash="exp_user": {"interests": []},
        raising=True,
    )
    two_platforms = {"reddit": ["x y z"], "amazon": ["u v w"]}
    exp = Exp02Fragments(two_platforms, holdout=[], tracker=_FakeTracker())
    assert set(exp.run().keys()) == {1, 2}  # pas de 3


def test_exp04_applies_each_rank(monkeypatch):
    seen_ranks = []

    def fake_run(self, platform_texts, user_hash="exp_user"):
        seen_ranks.append(self.lora_cfg["r"])
        return {"user_hash": user_hash, "interests": ["python"]}

    monkeypatch.setattr(
        "evaluation.baselines.BaselineConfig.run_pipeline", fake_run, raising=True
    )

    exp = Exp04LoraRank(PLATFORM_TEXTS, holdout=["python"], tracker=_FakeTracker())
    results = exp.run()

    assert set(results.keys()) == {4, 8, 16, 32}
    assert seen_ranks == [4, 8, 16, 32]  # l'ablation fait bien varier r


def test_exp03_recommendation_quality(monkeypatch):
    from evaluation.experiments.exp_03_recommendation import Exp03Recommendation

    profiles = {
        "federated": {"interests": ["ml"]},
        "centralized": {"interests": ["ml"]},
    }
    catalog = [{"id": "P1"}, {"id": "P2"}, {"id": "P3"}]
    exp = Exp03Recommendation(
        profiles, catalog, relevant_items=["P1", "P2"], tracker=_FakeTracker()
    )
    # reco factice : renvoie P1,P2,P3 dans l'ordre (pas d'appel Sentence-BERT)
    monkeypatch.setattr(
        exp,
        "_recommend",
        lambda profile, k: [{"item_id": i["id"]} for i in catalog][:k],
    )
    results = exp.run()

    assert set(results.keys()) == {"federated", "centralized"}
    # top-5 (3 items) P1,P2,P3 ; pertinents P1,P2 -> precision@5 = 2/3, ndcg parfait
    assert round(results["federated"]["precision_at_5"], 4) == round(2 / 3, 4)
    assert results["federated"]["ndcg_at_5"] == 1.0


def test_exp05_varies_sigma(monkeypatch):
    from evaluation.experiments.exp_05_dp import Exp05DifferentialPrivacy

    seen_sigmas = []

    def fake_run(self, platform_texts, user_hash="exp_user"):
        seen_sigmas.append(self.fed_cfg.get("dp_noise_sigma"))
        return {"user_hash": user_hash, "interests": ["python"]}

    monkeypatch.setattr(
        "evaluation.baselines.BaselineConfig.run_pipeline", fake_run, raising=True
    )

    exp = Exp05DifferentialPrivacy(
        PLATFORM_TEXTS, holdout=["python"], tracker=_FakeTracker()
    )
    results = exp.run()

    assert set(results.keys()) == {0.0, 0.05, 0.1, 0.2}
    assert seen_sigmas == [0.0, 0.05, 0.1, 0.2]  # DP appliqué à chaque niveau
    assert results[0.0]["ratio"] is None  # sigma=0 -> pas de ratio


def test_baseline_aggregate_applies_dp_noise():
    import pytest

    torch = pytest.importorskip("torch")
    from evaluation.baselines import FederatedConfig
    from maha_these.core.data_models import TrainerOutput

    out = TrainerOutput(
        agent_id="F1", lora_weights={"w": torch.zeros(200)}, dataset_size=10
    )
    # sans DP : θ reste nul ; avec DP : bruit gaussien ajouté
    assert FederatedConfig()._aggregate([out])["w"].abs().sum().item() == 0.0
    noisy = FederatedConfig(fed_cfg={"dp_noise_sigma": 0.5})._aggregate([out])
    assert noisy["w"].abs().sum().item() > 0.0
