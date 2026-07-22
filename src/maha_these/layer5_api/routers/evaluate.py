"""GET /api/v1/evaluate/comparison — métriques comparatives des configs."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["evaluate"])


@router.get("/evaluate/comparison")
async def get_comparison_metrics() -> dict:
    """Renvoie le tableau comparatif fédéré vs centralisé vs mono-source.

    TODO(Phase 3) : lire les résultats MLflow réels (EvaluationRunner).
    Renvoie pour l'instant une structure vide conforme au contrat.
    """
    return {
        "configs": ["federated", "centralized", "mono_source"],
        "metrics": {
            "precision_at_5": {},
            "semantic_coherence": {},
            "rouge_l": {},
            "ndcg_at_10": {},
        },
        "status": "not_computed",
    }
