"""POST /api/v1/reddit/profile — crawl Reddit réel → profil heuristique (RAM).

Utilise l'API Reddit (PRAW) avec les identifiants du ``.env`` pour collecter les
données publiques d'un utilisateur, en dérive un profil **sans LLM**
(``HeuristicProfileBuilder``), le stocke en RAM, puis vide la session. Le profil
peut ensuite être interrogé (``GET /profile/{hash}``) et alimente la reco.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from maha_these.core.session_buffer import SessionBuffer
from maha_these.layer3_profile.heuristic_profile import HeuristicProfileBuilder
from maha_these.layer3_profile.profile_store import ProfileStore

router = APIRouter(prefix="/api/v1/reddit", tags=["reddit"])


class RedditProfileRequest(BaseModel):
    username: str
    limit: int = 100


def _reddit_config(limit: int) -> dict:
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    if not client_id or client_id.startswith(("your_", "xxx")):
        raise HTTPException(
            status_code=400,
            detail="Identifiants Reddit manquants : renseigne REDDIT_CLIENT_ID / "
            "REDDIT_CLIENT_SECRET dans le fichier .env, puis relance l'API.",
        )
    return {
        "client_id": client_id,
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", ""),
        "user_agent": os.getenv("REDDIT_USER_AGENT", "FederatedProfiler/1.0"),
        "limit": limit,
    }


@router.post("/profile")
async def build_reddit_profile(request: RedditProfileRequest) -> dict:
    """Crawl Reddit → profil heuristique → RAM. Renvoie le profil généré."""
    from maha_these.layer1_crawling.reddit_crawler import RedditCrawlerAgent

    crawler = RedditCrawlerAgent(_reddit_config(request.limit))

    with SessionBuffer() as buf:  # RAM, effacée à la sortie du bloc
        try:
            result = crawler.run(request.username, buffer=buf)
        except Exception as exc:  # praw / réseau / utilisateur introuvable
            raise HTTPException(
                status_code=502, detail=f"Crawl Reddit échoué : {exc}"
            ) from exc

        data = buf.read("reddit") or {}
        profile = HeuristicProfileBuilder().build(data, result["user_hash"])
        ProfileStore.save(profile)

    return {
        "status": "success",
        "user_hash": profile["user_hash"],
        "n_items": result["n_items"],
        "interests": profile["interests"],
        "marketing_segments": profile["marketing_segments"],
    }
