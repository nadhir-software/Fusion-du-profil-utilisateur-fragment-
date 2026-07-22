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
    """Orchestration crawl -> (preprocess -> train -> aggregate -> profil).

    Exécutée en tâche de fond. La collecte se fait dans un ``SessionBuffer``
    **en RAM**, effacé en fin de session (aucune persistance des données).

    TODO(Phase 1/2) : enchaîner prétraitement -> fragments -> entraînement
    local (Δθ) -> agrégation -> génération de profil, tant que le buffer est
    vivant (dans ``OrchestrationAgent.run``).
    """
    from maha_these.core.orchestrator import OrchestrationAgent
    from maha_these.layer1_crawling import (
        AmazonCrawlerAgent,
        LinkedInCrawlerAgent,
        RedditCrawlerAgent,
    )

    orchestrator = OrchestrationAgent(
        {
            "reddit": RedditCrawlerAgent(),
            "linkedin": LinkedInCrawlerAgent(),
            "amazon": AmazonCrawlerAgent(),
        }
    )
    targets = {
        "reddit": reddit_username,
        "linkedin": linkedin_url or "",
        "amazon": amazon_profile_url or "",
    }
    return orchestrator.run(targets)


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_user(request: CrawlRequest, bg: BackgroundTasks) -> CrawlResponse:
    """Démarre le pipeline de crawling en arrière-plan (collecte en RAM)."""
    bg.add_task(
        run_full_pipeline,
        request.reddit_username,
        request.linkedin_url,
        request.amazon_profile_url,
    )
    return CrawlResponse(status="started", job_id=generate_job_id())
