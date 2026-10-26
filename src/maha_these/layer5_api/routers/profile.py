"""GET /api/v1/profile/{user_hash} — profil global unifié d'un utilisateur."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..dependencies import get_profile_store

router = APIRouter(prefix="/api/v1", tags=["profile"])


@router.get("/profiles")
async def list_profiles() -> dict:
    """Liste tous les profils du registre (résumé) — pour parcourir le dashboard."""
    profiles = get_profile_store().load_all()
    items = [
        {
            "user_hash": p.get("user_hash"),
            "interests": (p.get("interests") or [])[:4],
            "sector": (p.get("professional") or {}).get("sector"),
            "segments": (p.get("marketing_segments") or [])[:2],
            "platforms": p.get("platforms_covered") or [],
            "version": p.get("profile_version"),
        }
        for p in profiles
    ]
    items.sort(key=lambda x: (x["user_hash"] or ""))
    return {"count": len(items), "profiles": items}


@router.get("/profile/{user_hash}")
async def get_profile(user_hash: str) -> dict:
    """Retourne le profil unifié, ou 404 s'il n'existe pas."""
    store = get_profile_store()
    profile = store.load(user_hash)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
