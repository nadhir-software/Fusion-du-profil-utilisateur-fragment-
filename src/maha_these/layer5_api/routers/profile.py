"""GET /api/v1/profile/{user_hash} — profil global unifié d'un utilisateur."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..dependencies import get_profile_store

router = APIRouter(prefix="/api/v1", tags=["profile"])


@router.get("/profile/{user_hash}")
async def get_profile(user_hash: str) -> dict:
    """Retourne le profil unifié, ou 404 s'il n'existe pas."""
    store = get_profile_store()
    profile = store.load(user_hash)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
