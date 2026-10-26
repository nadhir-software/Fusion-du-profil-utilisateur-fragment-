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


# Profils de démo variés (hash, secteur, séniorité, compétences, intérêts,
# catégories d'achat, sensibilité prix, segments, plateformes, besoins implicites)
_DEMO_SPECS: list[tuple] = [
    (
        "demo_alice",
        "Tech",
        "senior",
        ["Python", "MLOps", "PyTorch"],
        ["machine learning", "cyclisme", "photographie", "cuisine"],
        ["électronique", "livres"],
        "moyenne",
        ["tech-enthusiast", "early-adopter"],
        ["reddit", "linkedin", "amazon"],
        ["formation en ligne", "matériel photo"],
    ),
    (
        "demo_bob",
        "Finance",
        "manager",
        ["Analyse", "Excel", "Risk"],
        ["finance", "immobilier", "voyages", "vin"],
        ["voyage", "luxe"],
        "faible",
        ["high-value", "traveler"],
        ["linkedin", "amazon"],
        ["conseil patrimonial", "cartes premium"],
    ),
    (
        "demo_carla",
        "Marketing",
        "junior",
        ["SEO", "Design", "Content"],
        ["mode", "beauté", "fitness", "cuisine"],
        ["mode", "beauté"],
        "moyenne",
        ["fashion-lover", "early-adopter"],
        ["reddit", "amazon"],
        ["abonnement sport", "cosmétiques bio"],
    ),
    (
        "demo_dan",
        "Tech",
        "senior",
        ["C++", "GPU", "Unity"],
        ["jeux vidéo", "informatique", "musique", "cinéma"],
        ["électronique", "gaming"],
        "moyenne",
        ["tech-enthusiast", "gamer"],
        ["reddit", "linkedin"],
        ["carte graphique", "casque gaming"],
    ),
    (
        "demo_eva",
        "Éducation",
        "confirmé",
        ["Pédagogie", "Rédaction"],
        ["écologie", "jardinage", "lecture", "randonnée"],
        ["maison", "livres"],
        "élevée",
        ["eco-conscious", "reader"],
        ["reddit", "amazon"],
        ["produits durables", "matériel outdoor"],
    ),
    (
        "demo_farah",
        "Santé",
        "confirmé",
        ["Coaching", "Nutrition", "Anatomie"],
        ["fitness", "course à pied", "nutrition", "yoga"],
        ["sport", "santé"],
        "moyenne",
        ["fitness-lover", "health-conscious"],
        ["reddit", "amazon"],
        ["montre cardio", "compléments"],
    ),
    (
        "demo_karim",
        "Restauration",
        "senior",
        ["Cuisine", "Pâtisserie", "Gestion"],
        ["gastronomie", "vin", "voyages", "cuisine du monde"],
        ["cuisine", "épicerie"],
        "faible",
        ["foodie", "high-value"],
        ["linkedin", "amazon"],
        ["robot cuiseur", "couteaux pro"],
    ),
    (
        "demo_lina",
        "Médias",
        "junior",
        ["Photographie", "Montage", "Storytelling"],
        ["photographie", "voyage", "art", "design"],
        ["photo", "voyage"],
        "moyenne",
        ["creative", "traveler"],
        ["reddit", "linkedin", "amazon"],
        ["objectif photo", "trépied"],
    ),
    (
        "demo_omar",
        "Tech",
        "junior",
        ["JavaScript", "React", "Node"],
        ["développement web", "startup", "productivité", "podcasts"],
        ["électronique", "livres"],
        "moyenne",
        ["tech-enthusiast", "early-adopter"],
        ["reddit", "linkedin"],
        ["clavier mécanique", "écran secondaire"],
    ),
    (
        "demo_sara",
        "Musique",
        "confirmé",
        ["Production", "Mixage", "DJ"],
        ["musique électronique", "audio", "concerts", "matériel hi-fi"],
        ["audio", "électronique"],
        "moyenne",
        ["audiophile", "creative"],
        ["reddit", "amazon"],
        ["casque studio", "carte son"],
    ),
    (
        "demo_youssef",
        "Automobile",
        "senior",
        ["Mécanique", "Diagnostic"],
        ["automobile", "mécanique", "sport auto", "bricolage"],
        ["auto", "outillage"],
        "moyenne",
        ["diy", "car-enthusiast"],
        ["reddit", "amazon"],
        ["outillage", "pièces détachées"],
    ),
    (
        "demo_nadia",
        "Éducation",
        "manager",
        ["Langues", "Traduction", "e-learning"],
        ["langues", "lecture", "voyages culturels", "histoire"],
        ["livres", "voyage"],
        "élevée",
        ["reader", "learner"],
        ["linkedin", "amazon"],
        ["liseuse", "cours en ligne"],
    ),
    (
        "demo_hedi",
        "Commerce",
        "junior",
        ["Vente", "Négociation"],
        ["football", "sport", "streaming", "sneakers"],
        ["mode", "sport"],
        "moyenne",
        ["sports-fan", "trend-follower"],
        ["reddit", "amazon"],
        ["maillot", "abonnement sport"],
    ),
    (
        "demo_ines",
        "Design",
        "confirmé",
        ["UX", "UI", "Figma", "Illustration"],
        ["design", "art", "décoration", "typographie"],
        ["maison", "art"],
        "moyenne",
        ["creative", "early-adopter"],
        ["linkedin", "amazon"],
        ["tablette graphique", "mobilier design"],
    ),
    (
        "demo_walid",
        "Finance",
        "senior",
        ["Trading", "Crypto", "Data"],
        ["crypto", "investissement", "technologie", "économie"],
        ["électronique", "livres"],
        "faible",
        ["high-value", "tech-enthusiast"],
        ["reddit", "linkedin"],
        ["hardware wallet", "abonnement data"],
    ),
    (
        "demo_maha",
        "Recherche",
        "confirmé",
        ["IA", "NLP", "Recherche", "Python"],
        ["intelligence artificielle", "apprentissage fédéré", "lecture", "café"],
        ["livres", "électronique"],
        "moyenne",
        ["researcher", "tech-enthusiast"],
        ["reddit", "linkedin", "amazon"],
        ["GPU", "articles scientifiques"],
    ),
]


def _demo_profiles() -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    profiles = []
    for (
        h,
        sector,
        sen,
        skills,
        interests,
        cats,
        price,
        segs,
        plats,
        needs,
    ) in _DEMO_SPECS:
        profiles.append(
            {
                "user_hash": h,
                "interests": interests,
                "needs": {"implicit": needs},
                "professional": {"sector": sector, "skills": skills, "seniority": sen},
                "consumption": {
                    "preferred_categories": cats,
                    "price_sensitivity": price,
                },
                "marketing_segments": segs,
                "platforms_covered": plats,
                "profile_version": "demo",
                "generated_at": now,
            }
        )
    return profiles


def generate_synthetic_profiles(count: int, seed: int = 42) -> list[dict]:
    """Génère + stocke ``count`` profils synthétiques (streamés en RAM)."""
    from maha_these.core.anonymizer import DataAnonymizer
    from maha_these.data_generation.synthetic import SyntheticDataGenerator
    from maha_these.layer3_profile.heuristic_profile import HeuristicProfileBuilder

    generator = SyntheticDataGenerator(seed)
    anonymizer = DataAnonymizer()
    builder = HeuristicProfileBuilder()

    created = []
    for i in range(count):
        raw = generator.generate_all(f"synthetic_user_{i}")
        data = anonymizer.anonymize(raw)  # hash + nettoyage PII
        profile = builder.build(data, data["user_hash"])
        ProfileStore.save(profile)
        created.append(profile)
    return created


def seed_startup(target: int, seed: int = 42) -> int:
    """Peuple le registre à ~``target`` profils : démos + synthétiques.

    Utilisé au démarrage de l'API (env ``DEV_SEED_ON_START``) pour offrir un
    registre « live » dès le boot, sans perdre le principe RAM-only.
    """
    for p in _demo_profiles():
        ProfileStore.save(p)
    remaining = max(0, target - len(_DEMO_SPECS))
    generate_synthetic_profiles(remaining, seed)
    return len(ProfileStore.load_all())


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
    created = generate_synthetic_profiles(request.count, request.seed)
    return {
        "status": "seeded",
        "count": len(created),
        "profiles": [
            {"user_hash": p["user_hash"], "interests": p["interests"][:5]}
            for p in created
        ],
    }


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
