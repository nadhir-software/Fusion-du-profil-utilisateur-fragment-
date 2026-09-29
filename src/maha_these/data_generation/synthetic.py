"""SyntheticDataGenerator — données synthétiques multi-plateformes.

Chaque "utilisateur" se voit attribuer de façon déterministe un *persona*
(dérivé du hash de son identifiant), qui pilote ses subreddits, mots-clés,
catégories d'achat et profil professionnel. La génération est **reproductible**
(seed fixe) — indispensable pour le protocole scientifique.

Les données produites ont exactement la forme des sorties des crawlers réels,
donc elles traversent le même pipeline (anonymisation → préprocessing →
fragments → LoRA → FedAvg → profil → reco).
"""

from __future__ import annotations

import hashlib
import random
from typing import Any

from maha_these.core.base_agent import BaseAgent
from maha_these.layer1_crawling.base_crawler import CrawlerAgent

# --------------------------------------------------------------------------- #
# Personas — profils-types cohérents à travers les plateformes.
# --------------------------------------------------------------------------- #
PERSONAS: list[dict[str, Any]] = [
    {
        "name": "tech_ml",
        "subreddits": ["MachineLearning", "datascience", "Python", "programming"],
        "keywords": [
            "pytorch",
            "model",
            "training",
            "dataset",
            "neural",
            "algorithm",
            "code",
            "gpu",
            "python",
            "learning",
        ],
        "amazon_categories": ["electronics", "books", "computers"],
        "products": ["GPU RTX 4070", "Deep Learning book", "mechanical keyboard"],
        "headline": "Data Scientist | Machine Learning Engineer",
        "skills": ["Python", "Machine Learning", "PyTorch", "MLOps"],
    },
    {
        "name": "fitness_cycling",
        "subreddits": ["cycling", "running", "fitness", "bicycling"],
        "keywords": [
            "training",
            "ride",
            "endurance",
            "cadence",
            "gear",
            "marathon",
            "recovery",
            "nutrition",
            "watts",
            "climb",
        ],
        "amazon_categories": ["sports", "outdoors", "health"],
        "products": ["carbon road bike", "running shoes", "heart rate monitor"],
        "headline": "Coach sportif | Passionné d'endurance",
        "skills": ["Coaching", "Nutrition", "Endurance", "Cyclisme"],
    },
    {
        "name": "foodie_cooking",
        "subreddits": ["cooking", "food", "recipes", "MealPrepSunday"],
        "keywords": [
            "recipe",
            "flavor",
            "kitchen",
            "baking",
            "sauce",
            "ingredients",
            "roast",
            "spices",
            "dish",
            "meal",
        ],
        "amazon_categories": ["kitchen", "home", "grocery"],
        "products": ["robot cuiseur", "chef knife set", "cast iron pan"],
        "headline": "Chef | Créateur de contenu culinaire",
        "skills": ["Cuisine", "Pâtisserie", "Food styling"],
    },
    {
        "name": "finance_invest",
        "subreddits": [
            "investing",
            "personalfinance",
            "stocks",
            "financialindependence",
        ],
        "keywords": [
            "portfolio",
            "dividend",
            "market",
            "index",
            "risk",
            "savings",
            "etf",
            "strategy",
            "returns",
            "budget",
        ],
        "amazon_categories": ["books", "office", "electronics"],
        "products": ["finance book", "premium notebook", "second monitor"],
        "headline": "Analyste financier | Investisseur",
        "skills": ["Finance", "Analyse", "Excel", "Gestion de risque"],
    },
    {
        "name": "gamer_tech",
        "subreddits": ["gaming", "pcgaming", "buildapc", "games"],
        "keywords": [
            "fps",
            "graphics",
            "console",
            "build",
            "controller",
            "release",
            "gameplay",
            "rig",
            "monitor",
            "latency",
        ],
        "amazon_categories": ["electronics", "gaming", "computers"],
        "products": ["gaming headset", "graphics card", "gaming chair"],
        "headline": "Développeur jeux vidéo | Gamer",
        "skills": ["C++", "Unity", "GPU", "Game Design"],
    },
    {
        "name": "eco_outdoor",
        "subreddits": ["ZeroWaste", "hiking", "gardening", "sustainability"],
        "keywords": [
            "sustainable",
            "trail",
            "compost",
            "reusable",
            "nature",
            "plants",
            "hiking",
            "solar",
            "recycle",
            "outdoor",
        ],
        "amazon_categories": ["outdoors", "garden", "home"],
        "products": ["reusable bottle", "hiking backpack", "compost bin"],
        "headline": "Consultant développement durable",
        "skills": ["Écologie", "Jardinage", "Rédaction"],
    },
]

_CONNECTORS = [
    "really",
    "the",
    "and",
    "with",
    "for",
    "great",
    "best",
    "new",
    "using",
    "about",
    "this",
    "love",
    "recommend",
]


class SyntheticDataGenerator:
    """Génère des données synthétiques déterministes par utilisateur."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    # -- déterminisme -------------------------------------------------------- #
    def _rng(self, username: str) -> random.Random:
        return random.Random(f"{self.seed}:{username}")

    def persona(self, username: str) -> dict[str, Any]:
        h = int(hashlib.sha256(username.encode()).hexdigest(), 16)
        return PERSONAS[h % len(PERSONAS)]

    def _sentence(self, rng: random.Random, persona: dict, n_words: int) -> str:
        pool = persona["keywords"] * 2 + _CONNECTORS
        return " ".join(rng.choice(pool) for _ in range(n_words)).capitalize()

    # -- générateurs par plateforme ----------------------------------------- #
    def generate_reddit(
        self, username: str, n_posts: int = 15, n_comments: int = 30
    ) -> dict[str, Any]:
        rng = self._rng(username)
        persona = self.persona(username)
        posts = [
            {
                "id": f"p{i}",
                "title": self._sentence(rng, persona, 6),
                "body": self._sentence(rng, persona, 22),
                "subreddit": rng.choice(persona["subreddits"]),
                "score": rng.randint(0, 500),
                "created_utc": 1_700_000_000 + i * 1000,
                "type": "post",
            }
            for i in range(n_posts)
        ]
        comments = [
            {
                "id": f"c{i}",
                "body": self._sentence(rng, persona, 14),
                "subreddit": rng.choice(persona["subreddits"]),
                "score": rng.randint(0, 200),
                "created_utc": 1_700_000_000 + i * 500,
                "type": "comment",
            }
            for i in range(n_comments)
        ]
        return {"username": username, "posts": posts, "comments": comments}

    def generate_amazon(self, username: str, n_reviews: int = 12) -> dict[str, Any]:
        rng = self._rng(username)
        persona = self.persona(username)
        reviews = [
            {
                "product": rng.choice(persona["products"]),
                "category": rng.choice(persona["amazon_categories"]),
                "rating": rng.choice([3, 4, 4, 5, 5]),
                "text": self._sentence(rng, persona, 18),
                "type": "review",
            }
            for _ in range(n_reviews)
        ]
        return {"username": username, "reviews": reviews}

    def generate_linkedin(self, username: str) -> dict[str, Any]:
        rng = self._rng(username)
        persona = self.persona(username)
        return {
            "username": username,
            "profile": [
                {
                    "headline": persona["headline"],
                    "text": self._sentence(rng, persona, 25),
                    "location": rng.choice(["Sfax", "Tunis", "Paris", "Remote"]),
                }
            ],
            "skills": [{"name": s} for s in persona["skills"]],
        }

    def generate_all(self, username: str) -> dict[str, Any]:
        """Fusionne les 3 plateformes en un enregistrement brut unique."""
        merged: dict[str, Any] = {"username": username}
        for part in (
            self.generate_reddit(username),
            self.generate_amazon(username),
            self.generate_linkedin(username),
        ):
            merged.update({k: v for k, v in part.items() if k != "username"})
        return merged


# --------------------------------------------------------------------------- #
# Crawlers synthétiques — remplacent les crawlers réseau dans le pipeline.
# --------------------------------------------------------------------------- #
class _SyntheticCrawler(CrawlerAgent):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.generator = SyntheticDataGenerator(self.config.get("seed", 42))


class SyntheticRedditCrawler(_SyntheticCrawler):
    platform = "reddit"
    name = "synthetic_reddit"

    def crawl_user(self, identifier: str) -> dict[str, Any]:
        return self.generator.generate_reddit(identifier)


class SyntheticLinkedInCrawler(_SyntheticCrawler):
    platform = "linkedin"
    name = "synthetic_linkedin"

    def crawl_user(self, identifier: str) -> dict[str, Any]:
        return self.generator.generate_linkedin(identifier)


class SyntheticAmazonCrawler(_SyntheticCrawler):
    platform = "amazon"
    name = "synthetic_amazon"

    def crawl_user(self, identifier: str) -> dict[str, Any]:
        return self.generator.generate_amazon(identifier)


def build_synthetic_pipeline(config: dict[str, Any] | None = None):
    """Pipeline fédéré complet alimenté par des données synthétiques.

    Permet de faire tourner crawl→train→profil de bout en bout (entraînement
    réel LoRA si la pile ``[ai]`` + GPU sont disponibles), sans aucune donnée
    réelle.
    """
    from maha_these.pipeline import FederatedProfilingPipeline

    crawlers: dict[str, BaseAgent] = {
        "reddit": SyntheticRedditCrawler(config),
        "linkedin": SyntheticLinkedInCrawler(config),
        "amazon": SyntheticAmazonCrawler(config),
    }
    return FederatedProfilingPipeline(crawlers, config)
