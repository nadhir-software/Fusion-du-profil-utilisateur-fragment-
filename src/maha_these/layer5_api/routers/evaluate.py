"""GET /api/v1/evaluate/comparison — métriques comparatives des configs.

Lit le dernier résumé écrit par ``scripts/run_all_experiments.py`` dans
``reports/experiments/results_*.json`` et le transpose au format attendu par le
dashboard (onglet Évaluation). Tant qu'aucune campagne n'a tourné, renvoie une
structure vide (``status="not_computed"``).
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["evaluate"])

# src/maha_these/layer5_api/routers/evaluate.py → remonter à la racine du dépôt
_REPO = Path(__file__).resolve().parents[4]
_RESULTS_DIR = _REPO / "reports" / "experiments"

_EMPTY = {
    "configs": ["federated", "centralized", "mono_source"],
    "metrics": {
        "precision_at_5": {},
        "ndcg_at_10": {},
        "precision_at_1": {},
    },
    "status": "not_computed",
}


def _latest_results_file() -> Path | None:
    if not _RESULTS_DIR.is_dir():
        return None
    files = sorted(_RESULTS_DIR.glob("results_*.json"))
    return files[-1] if files else None


def _to_comparison(payload: dict) -> dict:
    """Transpose ``results.exp_01`` -> {configs, metrics[metric][config]}."""
    exp01 = (payload.get("results") or {}).get("exp_01") or {}
    if not exp01:
        return _EMPTY

    configs = list(exp01.keys())
    metrics: dict[str, dict[str, float]] = {}
    for config, config_metrics in exp01.items():
        for metric, value in (config_metrics or {}).items():
            metrics.setdefault(metric, {})[config] = round(float(value), 4)

    return {
        "configs": configs,
        "metrics": metrics,
        "status": "computed",
        "mode": payload.get("mode", "unknown"),
        "note": payload.get("note", ""),
        "generated_at": payload.get("generated_at", ""),
    }


@router.get("/evaluate/comparison")
async def get_comparison_metrics() -> dict:
    """Tableau comparatif fédéré vs centralisé vs mono-source (EXP-01)."""
    latest = _latest_results_file()
    if latest is None:
        return _EMPTY
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _EMPTY
    return _to_comparison(payload)
