"""Application FastAPI — point d'entrée de l'API REST.

Assemble les 7 endpoints via les routeurs modulaires. Lancement :
    uvicorn maha_these.layer5_api.main:app --reload

CORS activé pour le front React en développement (Vite, http://localhost:5173).
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import crawl, dev, evaluate, profile, reddit, recommend, segments

# Charge les identifiants du .env (Reddit, HuggingFace…) dans l'environnement.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

app = FastAPI(title="Federated User Profiling API", version="1.0")

# CORS — front React en dev. En production, restreindre `allow_origins`.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crawl.router)
app.include_router(profile.router)
app.include_router(recommend.router)
app.include_router(segments.router)
app.include_router(evaluate.router)
app.include_router(reddit.router)  # crawl Reddit réel -> profil heuristique
app.include_router(dev.router)  # DEV ONLY — seed de profils de démo


@app.on_event("startup")
async def _seed_registry_on_start() -> None:
    """Registre « live » au démarrage si ``DEV_SEED_ON_START`` est défini.

    Ex. ``DEV_SEED_ON_START=200`` → 16 profils démo + synthétiques pour
    atteindre 200. Reste RAM-only (rien n'est écrit sur disque).
    """
    target = os.getenv("DEV_SEED_ON_START")
    if not target:
        return
    try:
        n = dev.seed_startup(int(target))
        print(f"[startup] registre peuplé : {n} profils (DEV_SEED_ON_START={target})")
    except Exception as exc:  # noqa: BLE001 — best effort au démarrage
        print(f"[startup] seed ignoré : {exc}")


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Sonde de disponibilité."""
    return {"status": "ok"}
