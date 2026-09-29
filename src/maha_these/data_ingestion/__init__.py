"""Ingestion de catalogues d'items depuis des datasets publics sous licence.

Sert à alimenter le moteur de recommandation avec de VRAIS items, sans scraping.
Source par défaut : Amazon Reviews 2023 (McAuley/UCSD), publié pour la recherche.
"""

from .amazon_reviews import download_category, load_catalog

__all__ = ["download_category", "load_catalog"]
