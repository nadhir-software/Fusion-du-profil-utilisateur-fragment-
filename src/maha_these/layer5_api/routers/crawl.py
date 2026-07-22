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
) -> None:
    """Orchestration crawl -> preprocess -> train -> aggregate -> profile.

    Exécutée en tâche de fond. TODO(Phase 1/2) : brancher l'orchestrateur réel
    (crawlers, trainers, agrégateur, générateur de profil).
    """
    # TODO: implémenter l'orchestration complète du pipeline.
    raise NotImplementedError("run_full_pipeline() — orchestration à brancher.")


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_user(request: CrawlRequest, bg: BackgroundTasks) -> CrawlResponse:
    """Démarre le pipeline de crawling en arrière-plan."""
    bg.add_task(
        run_full_pipeline,
        request.reddit_username,
        request.linkedin_url,
        request.amazon_profile_url,
    )
    return CrawlResponse(status="started", job_id=generate_job_id())
