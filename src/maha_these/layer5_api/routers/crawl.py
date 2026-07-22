"""POST /api/v1/crawl — lance le crawling multi-plateformes d'un utilisateur."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from ..dependencies import generate_job_id
from ..schemas import CrawlRequest, CrawlResponse

router = APIRouter(prefix="/api/v1", tags=["crawl"])


def run_full_pipeline(
    reddit_username: str,
    linkedin_url: str | None = None,
    amazon_profile_url: str | None = None,
) -> dict:
    """Pipeline complet : crawl -> preprocess -> train -> aggregate -> profil.

    Exécutée en tâche de fond, **dans le process API** (donc le profil généré
    peuple bien le registre RAM lu par ``GET /profile/{hash}``). La collecte se
    fait dans un ``SessionBuffer`` effacé en fin de session (aucune persistance
    des données brutes). Nécessite la pile ``[ai]`` + ``[crawl]`` et des
    identifiants Reddit (voir RUNBOOK.md).
    """
    from maha_these.pipeline import build_default_pipeline

    pipeline = build_default_pipeline()
    targets = {
        "reddit": reddit_username,
        "linkedin": linkedin_url or "",
        "amazon": amazon_profile_url or "",
    }
    return pipeline.run(targets)


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_user(request: CrawlRequest, bg: BackgroundTasks) -> CrawlResponse:
    """Démarre le pipeline complet en arrière-plan (collecte en RAM).

    Renvoie immédiatement le ``user_hash`` unifié sous lequel le profil sera
    stocké une fois le pipeline terminé (à interroger via GET /profile/{hash}).
    """
    from maha_these.pipeline import unified_user_hash

    targets = {
        "reddit": request.reddit_username,
        "linkedin": request.linkedin_url or "",
        "amazon": request.amazon_profile_url or "",
    }
    bg.add_task(
        run_full_pipeline,
        request.reddit_username,
        request.linkedin_url,
        request.amazon_profile_url,
    )
    return CrawlResponse(
        status="started",
        job_id=generate_job_id(),
        user_hash=unified_user_hash(targets),
    )
