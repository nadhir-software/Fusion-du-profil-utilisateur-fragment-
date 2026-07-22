"""GET /api/v1/profiles/segments — vue d'ensemble des segments marketing."""

from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import get_profile_store

router = APIRouter(prefix="/api/v1", tags=["segments"])


@router.get("/profiles/segments")
async def list_segments() -> dict:
    """Agrège les segments marketing présents dans les profils stockés."""
    profiles = get_profile_store().load_all()
    counts: dict[str, int] = {}
    for p in profiles:
        for seg in p.get("marketing_segments", []):
            counts[seg] = counts.get(seg, 0) + 1
    segments = [
        {"segment": seg, "count": n}
        for seg, n in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return {"segments": segments, "total_profiles": len(profiles)}
