"""Tests du runner unique (scripts/run_all_experiments.py) — mode smoke.

Vérifie le **câblage** de bout en bout sans GPU ni torch : préparation des
données synthétiques → 5 campagnes → métriques. Les chiffres ne sont pas
scientifiques (mode smoke), on teste la chaîne, pas les résultats.
"""

import importlib.util
from pathlib import Path

_RUNNER = Path(__file__).resolve().parents[2] / "scripts" / "run_all_experiments.py"
_spec = importlib.util.spec_from_file_location("run_all_experiments", _RUNNER)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)


def test_prepare_data_has_three_platforms():
    platform_texts, holdout, persona = runner.prepare_data(seed=42, user="user_0")
    assert set(platform_texts) == {"reddit", "amazon", "linkedin"}
    assert all(platform_texts.values())  # aucune plateforme vide
    assert holdout and "name" in persona


def test_prepare_data_is_deterministic():
    a = runner.prepare_data(42, "user_3")
    b = runner.prepare_data(42, "user_3")
    assert a[0] == b[0] and a[2]["name"] == b[2]["name"]


def test_build_catalog_marks_relevant_items():
    catalog, relevant = runner.build_catalog("tech_ml")
    assert len(catalog) == 18  # 6 personas × 3 items
    assert relevant and all(i.startswith("tech_ml:") for i in relevant)


def test_smoke_profile_captures_persona_signal():
    platform_texts, holdout, _ = runner.prepare_data(42, "user_0")
    profile = runner._smoke_profile(platform_texts, "hash")
    # les intérêts extraits recoupent la vérité terrain du persona
    assert set(profile["interests"]) & set(holdout)


def test_smoke_campaigns_wiring(monkeypatch):
    import evaluation.baselines as baselines

    original = baselines.BaselineConfig.run_pipeline
    try:
        platform_texts, holdout, persona = runner.prepare_data(42, "user_0")
        runner.install_smoke_patches(None)
        results = runner.run_campaigns(
            platform_texts, holdout, persona, "smoke", runner._NullTracker()
        )
    finally:
        baselines.BaselineConfig.run_pipeline = original  # pas de fuite globale

    assert set(results) == {"exp_01", "exp_02", "exp_03", "exp_04", "exp_05"}
    # EXP-01 : 3 configs comparées
    assert set(results["exp_01"]) == {"federated", "centralized", "mono_source"}
    # EXP-02 : 3 tailles de fragments
    assert set(results["exp_02"]) == {1, 2, 3}
    # EXP-04 : 4 rangs LoRA
    assert set(results["exp_04"]) == {4, 8, 16, 32}
    # EXP-03 : reco fédéré recoupe la vérité terrain (câblage OK)
    assert results["exp_03"]["federated"]["ndcg_at_5"] > 0.0


def test_ai_stack_check_returns_bool():
    assert isinstance(runner.ai_stack_available(), bool)
