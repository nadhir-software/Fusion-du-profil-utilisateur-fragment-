"""Routes de développement — injection de profils de démo en RAM.

⚠️ DEV ONLY. Ces routes peuplent le registre RAM (``ProfileStore``) avec des
profils factices, afin de visualiser le dashboard **sans** lancer le pipeline
complet (crawl → preprocess → train → profil), qui nécessite la pile ML lourde.
À désactiver en production.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from maha_these.layer3_profile.profile_store import ProfileStore

router = APIRouter(prefix="/api/v1/dev", tags=["dev"])


class SyntheticRequest(BaseModel):
    count: int = 5
    seed: int = 42


class ReviewsProfilesRequest(BaseModel):
    category: str = "Magazine_Subscriptions"
    max_records: int = 100_000
    max_users: int = 50
    min_reviews: int = 3


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


@router.post("/synthetic")
async def seed_synthetic(request: SyntheticRequest) -> dict:
    """Génère ``count`` profils synthétiques multi-plateformes (conforme).

    Données synthétiques (aucun scraping) → anonymisation → profil heuristique
    (Reddit + Amazon + LinkedIn) → RAM. Peuple le dashboard avec des profils
    réalistes et variés, sans GPU. Reproductible (``seed``).
    """
    from maha_these.core.anonymizer import DataAnonymizer
    from maha_these.data_generation.synthetic import SyntheticDataGenerator
    from maha_these.layer3_profile.heuristic_profile import HeuristicProfileBuilder

    generator = SyntheticDataGenerator(request.seed)
    anonymizer = DataAnonymizer()
    builder = HeuristicProfileBuilder()

    created = []
    for i in range(request.count):
        raw = generator.generate_all(f"synthetic_user_{i}")
        data = anonymizer.anonymize(raw)  # hash + nettoyage PII
        profile = builder.build(data, data["user_hash"])
        ProfileStore.save(profile)
        created.append(
            {"user_hash": profile["user_hash"], "interests": profile["interests"][:5]}
        )

    return {"status": "seeded", "count": len(created), "profiles": created}


@router.post("/reviews-profiles")
async def build_reviews_profiles(request: ReviewsProfilesRequest) -> dict:
    """Construit de VRAIS profils depuis les avis Amazon (dataset McAuley).

    Streame les interactions user-item, groupe par utilisateur, construit un
    profil par utilisateur **un à un en RAM** (SessionBuffer, effacé après),
    puis stocke les profils. Peuple le dashboard avec de vrais profils.
    """
    from maha_these.data_ingestion.amazon_reviews import (
        download_category,
        download_reviews,
        load_catalog,
    )
    from maha_these.data_ingestion.review_profiles import build_profiles_from_reviews

    meta_path = download_category(request.category)
    catalog_index = {item["id"]: item for item in load_catalog(meta_path)}
    reviews_path = download_reviews(request.category)

    profiles = build_profiles_from_reviews(
        reviews_path,
        catalog_index=catalog_index,
        max_records=request.max_records,
        max_users=request.max_users,
        min_reviews=request.min_reviews,
    )
    for profile in profiles:
        ProfileStore.save(profile)

    return {
        "status": "seeded",
        "count": len(profiles),
        "category": request.category,
        "sample": [
            {"user_hash": p["user_hash"], "interests": p["interests"][:5]}
            for p in profiles[:5]
        ],
    }
