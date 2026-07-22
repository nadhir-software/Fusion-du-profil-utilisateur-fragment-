"""Routes de développement — injection de profils de démo en RAM.

⚠️ DEV ONLY. Ces routes peuplent le registre RAM (``ProfileStore``) avec des
profils factices, afin de visualiser le dashboard **sans** lancer le pipeline
complet (crawl → preprocess → train → profil), qui nécessite la pile ML lourde.
À désactiver en production.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from maha_these.layer3_profile.profile_store import ProfileStore

router = APIRouter(prefix="/api/v1/dev", tags=["dev"])


def _demo_profiles() -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    base = {"profile_version": "demo", "generated_at": now}
    return [
        {
            **base,
            "user_hash": "demo_alice",
            "interests": ["machine learning", "cyclisme", "photographie", "cuisine"],
            "needs": {"implicit": ["formation en ligne", "matériel photo"]},
            "professional": {
                "sector": "Tech",
                "skills": ["Python", "MLOps", "PyTorch"],
                "seniority": "senior",
            },
            "consumption": {
                "preferred_categories": ["électronique", "livres"],
                "price_sensitivity": "moyenne",
            },
            "marketing_segments": ["tech-enthusiast", "early-adopter"],
            "platforms_covered": ["reddit", "linkedin", "amazon"],
        },
        {
            **base,
            "user_hash": "demo_bob",
            "interests": ["finance", "immobilier", "voyages", "vin"],
            "needs": {"implicit": ["conseil patrimonial", "cartes premium"]},
            "professional": {
                "sector": "Finance",
                "skills": ["Analyse", "Excel", "Risk"],
                "seniority": "manager",
            },
            "consumption": {
                "preferred_categories": ["voyage", "luxe"],
                "price_sensitivity": "faible",
            },
            "marketing_segments": ["high-value", "traveler"],
            "platforms_covered": ["linkedin", "amazon"],
        },
        {
            **base,
            "user_hash": "demo_carla",
            "interests": ["mode", "beauté", "fitness", "cuisine"],
            "needs": {"implicit": ["abonnement sport", "cosmétiques bio"]},
            "professional": {
                "sector": "Marketing",
                "skills": ["SEO", "Design", "Content"],
                "seniority": "junior",
            },
            "consumption": {
                "preferred_categories": ["mode", "beauté"],
                "price_sensitivity": "moyenne",
            },
            "marketing_segments": ["fashion-lover", "early-adopter"],
            "platforms_covered": ["reddit", "amazon"],
        },
        {
            **base,
            "user_hash": "demo_dan",
            "interests": ["jeux vidéo", "informatique", "musique", "cinéma"],
            "needs": {"implicit": ["carte graphique", "casque gaming"]},
            "professional": {
                "sector": "Tech",
                "skills": ["C++", "GPU", "Unity"],
                "seniority": "senior",
            },
            "consumption": {
                "preferred_categories": ["électronique", "gaming"],
                "price_sensitivity": "moyenne",
            },
            "marketing_segments": ["tech-enthusiast", "gamer"],
            "platforms_covered": ["reddit", "linkedin"],
        },
        {
            **base,
            "user_hash": "demo_eva",
            "interests": ["écologie", "jardinage", "lecture", "randonnée"],
            "needs": {"implicit": ["produits durables", "matériel outdoor"]},
            "professional": {
                "sector": "Éducation",
                "skills": ["Pédagogie", "Rédaction"],
                "seniority": "confirmé",
            },
            "consumption": {
                "preferred_categories": ["maison", "livres"],
                "price_sensitivity": "élevée",
            },
            "marketing_segments": ["eco-conscious", "reader"],
            "platforms_covered": ["reddit", "amazon"],
        },
    ]


@router.post("/seed")
async def seed_demo() -> dict:
    """Injecte des profils de démo dans le registre RAM (dev only)."""
    profiles = _demo_profiles()
    for p in profiles:
        ProfileStore.save(p)
    return {
        "status": "seeded",
        "count": len(profiles),
        "user_hashes": [p["user_hash"] for p in profiles],
    }


@router.delete("/seed")
async def clear_demo() -> dict:
    """Vide le registre RAM des profils."""
    ProfileStore.clear()
    return {"status": "cleared"}
