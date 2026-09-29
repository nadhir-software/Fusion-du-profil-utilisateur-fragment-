"""Génération de données synthétiques (conforme, reproductible).

Produit des données réalistes multi-plateformes (Reddit-like, Amazon-like,
LinkedIn-like) à la MÊME forme que les crawlers, pour faire tourner le pipeline
complet sans collecter de données réelles (aucun scraping, aucun risque légal).
"""

from .synthetic import (
    SyntheticAmazonCrawler,
    SyntheticDataGenerator,
    SyntheticLinkedInCrawler,
    SyntheticRedditCrawler,
    build_synthetic_pipeline,
)

__all__ = [
    "SyntheticDataGenerator",
    "SyntheticRedditCrawler",
    "SyntheticLinkedInCrawler",
    "SyntheticAmazonCrawler",
    "build_synthetic_pipeline",
]
