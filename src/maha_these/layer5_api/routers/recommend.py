"""POST /api/v1/recommend/user + /campaign — recommandations dual-axe."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..dependencies import get_profile_store, get_recommender
from ..schemas import CampaignRequest, UserRecoRequest

router = APIRouter(prefix="/api/v1", tags=["recommend"])


@router.post("/recommend/user")
async def recommend_to_user(request: UserRecoRequest) -> dict:
    """Axe 1 : recommandations personnalisées pour un utilisateur."""
    profile = get_profile_store().load(request.user_hash)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    recommendations = get_recommender().recommend_to_user(
        profile, request.catalog, top_k=request.top_k
    )
    return {"recommendations": recommendations, "user_hash": request.user_hash}


@router.post("/recommend/campaign")
async def find_campaign_targets(request: CampaignRequest) -> dict:
    """Axe 2 : segments de profils cibles pour une campagne marketing."""
    all_profiles = get_profile_store().load_all()
    segments = get_recommender().find_target_segments(
        request.campaign, all_profiles, threshold=request.threshold
    )
    return {"segments": segments, "total_profiles_analyzed": len(all_profiles)}
