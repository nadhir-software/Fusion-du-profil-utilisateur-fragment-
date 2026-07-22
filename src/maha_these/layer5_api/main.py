"""Application FastAPI — point d'entrée de l'API REST.

Assemble les 7 endpoints via les routeurs modulaires. Lancement :
    uvicorn maha_these.layer5_api.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from .routers import crawl, evaluate, profile, recommend, segments

app = FastAPI(title="Federated User Profiling API", version="1.0")

app.include_router(crawl.router)
app.include_router(profile.router)
app.include_router(recommend.router)
app.include_router(segments.router)
app.include_router(evaluate.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Sonde de disponibilité."""
    return {"status": "ok"}
