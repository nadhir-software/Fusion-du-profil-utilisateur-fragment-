"""AmazonCrawlerAgent — collecte d'avis publics via Playwright + BeautifulSoup.

Sprint 1.1 (EN COURS). Collecte les avis/notes publics d'un profil, les
anonymise puis les stocke dans un silo isolé. Signal ``purchase``.

⚠️ Respecter les CGU Amazon et le RGPD : uniquement des avis publics.
La logique de scraping reste à implémenter (TODO Sprint 1.1).
"""

from __future__ import annotations

from typing import Any

from .base_crawler import CrawlerAgent


class AmazonCrawlerAgent(CrawlerAgent):
    """Crawler Amazon (Playwright + BeautifulSoup)."""

    platform = "amazon"
    name = "amazon_crawler"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.limit_reviews = self.config.get("limit_reviews", 50)

    def crawl_user(self, identifier: str) -> dict[str, Any]:
        """Collecte les avis publics (produit, catégorie, note, texte).

        Args:
            identifier: URL du profil public Amazon.

        Returns:
            dict ``{"username": ..., "reviews": [...]}``.
        """
        # TODO(Sprint 1.1): implémenter la collecte réelle avec Playwright,
        #   parser le HTML via BeautifulSoup, respecter le RateLimiter.
        raise NotImplementedError(
            "AmazonCrawlerAgent.crawl_user() n'est pas encore implémenté "
            "(Sprint 1.1). Voir la checklist du plan de développement."
        )
