"""LinkedInCrawlerAgent — collecte de profils publics via MCP / Playwright.

Sprint 1.1 (EN COURS). Deux modes possibles (config ``method``) :
- "mcp"        : via un serveur MCP LinkedIn (voir mcp_client.py).
- "playwright" : navigation headless sur les profils publics.

⚠️ Respecter les CGU LinkedIn et la législation (RGPD) : uniquement des
profils/données publics, anonymisés immédiatement via DataAnonymizer.
La logique de scraping reste à implémenter (TODO Sprint 1.1).
"""

from __future__ import annotations

from typing import Any

from .base_crawler import CrawlerAgent


class LinkedInCrawlerAgent(CrawlerAgent):
    """Crawler LinkedIn (MCP ou Playwright)."""

    platform = "linkedin"
    name = "linkedin_crawler"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.method = self.config.get("method", "playwright")

    def crawl_user(self, identifier: str) -> dict[str, Any]:
        """Collecte headline, résumé, secteur et compétences publics.

        Args:
            identifier: URL du profil public LinkedIn.

        Returns:
            dict ``{"username": ..., "profile": [...], "skills": [...]}``.
        """
        # TODO(Sprint 1.1): implémenter la collecte réelle.
        #   - method == "playwright": lancer un navigateur headless,
        #     naviguer vers `identifier`, extraire les champs publics via
        #     BeautifulSoup, gérer le rate limiting (RateLimiter).
        #   - method == "mcp": déléguer à MCPClient.
        raise NotImplementedError(
            "LinkedInCrawlerAgent.crawl_user() n'est pas encore implémenté "
            "(Sprint 1.1). Voir la checklist du plan de développement."
        )
