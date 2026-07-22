"""LinkedInCrawlerAgent — collecte de profils publics via Playwright / MCP.

Deux modes possibles (config ``method``) :
- "playwright" : navigation headless sur la page publique du profil, puis
  extraction des champs publics via BeautifulSoup.
- "mcp"        : délégation à un serveur MCP LinkedIn (non branché — Phase 1).

⚠️ Confidentialité & conformité : seules des données **publiques** sont
collectées, et elles sont anonymisées immédiatement par ``DataAnonymizer``
(via ``CrawlerAgent.run``) AVANT tout stockage. Le champ libre du résumé est
placé sous la clé ``text`` afin d'être nettoyé de ses PII résiduels.
Respecter les CGU LinkedIn et le RGPD reste de la responsabilité de
l'utilisateur du crawler.

Note : la structure HTML de LinkedIn et ses protections anti-bot évoluent ;
les sélecteurs ci-dessous privilégient les métadonnées Open Graph (stables)
avec repli sur le DOM. Ils peuvent nécessiter un ajustement.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from .base_crawler import CrawlerAgent
from .rate_limiter import RateLimiter

_HANDLE_RE = re.compile(r"/in/([^/?#]+)")


class LinkedInCrawlerAgent(CrawlerAgent):
    """Crawler LinkedIn (Playwright + BeautifulSoup, ou MCP)."""

    platform = "linkedin"
    name = "linkedin_crawler"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.method = self.config.get("method", "playwright")
        self.headless = self.config.get("headless", True)
        self.timeout_ms = self.config.get("timeout_ms", 30_000)
        self.max_skills = self.config.get("max_skills", 50)
        self.rate_limiter = RateLimiter(
            rate=self.config.get("requests_per_minute", 10), per=60.0
        )

    # ------------------------------------------------------------------ #
    # API publique
    # ------------------------------------------------------------------ #
    def crawl_user(self, identifier: str) -> dict[str, Any]:
        """Collecte headline, résumé, localisation et compétences publics.

        Args:
            identifier: URL du profil public LinkedIn (``https://.../in/slug``).

        Returns:
            dict ``{"username": handle, "profile": [ {...} ], "skills": [...]}``
            NON anonymisé — l'anonymisation est appliquée par :meth:`run`.
        """
        if self.method == "mcp":
            # TODO(Phase 1): déléguer à MCPClient une fois le transport branché.
            raise NotImplementedError(
                "Mode 'mcp' non branché ; utilisez method='playwright'."
            )

        html = self._fetch_html(identifier)
        profile = self._parse_profile(html)
        skills = self._parse_skills(html)
        return {
            "username": self._handle_from_url(identifier),
            "profile": [profile],
            "skills": skills,
        }

    # ------------------------------------------------------------------ #
    # Helpers — réseau
    # ------------------------------------------------------------------ #
    def _fetch_html(self, url: str) -> str:
        """Récupère le HTML rendu de la page profil via Playwright."""
        try:
            from playwright.sync_api import sync_playwright  # import paresseux
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "playwright est requis pour LinkedInCrawlerAgent. "
                'Installez l\'extra : pip install -e ".[crawl]" '
                "puis : python -m playwright install chromium"
            ) from exc

        self.rate_limiter.acquire()  # respecter la limite de débit
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            try:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                return page.content()
            finally:
                browser.close()

    # ------------------------------------------------------------------ #
    # Helpers — parsing (purs, testables hors-ligne)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _handle_from_url(url: str) -> str:
        """Extrait le slug public d'une URL LinkedIn (``/in/<slug>``).

        Repli sur le chemin ou l'URL brute si le motif n'est pas trouvé.
        """
        match = _HANDLE_RE.search(url)
        if match:
            return match.group(1)
        path = urlparse(url).path.strip("/")
        return path or url

    def _parse_profile(self, html: str) -> dict[str, Any]:
        """Extrait les champs profil publics depuis le HTML.

        Stratégie : métadonnées Open Graph d'abord (stables), repli DOM.
        """
        soup = self._soup(html)

        headline = self._meta(soup, "og:title") or self._text(soup, "h1")
        summary = self._meta(soup, "og:description") or self._text(
            soup, "section.summary, div.about, #about"
        )
        location = self._text(
            soup, ".text-body-small.inline, .profile-location, [class*='location']"
        )

        return {
            "headline": headline,
            "text": summary,  # champ libre -> nettoyé par l'anonymiseur
            "location": location,
        }

    def _parse_skills(self, html: str) -> list[dict[str, str]]:
        """Extrait la liste des compétences publiques (best-effort)."""
        soup = self._soup(html)
        selectors = [
            "[data-field='skill'] span",
            ".skill-category-entity__name span",
            "section#skills li span[aria-hidden='true']",
        ]
        names: list[str] = []
        for selector in selectors:
            for node in soup.select(selector):
                name = node.get_text(strip=True)
                if name and name not in names:
                    names.append(name)
            if names:
                break
        return [{"name": n} for n in names[: self.max_skills]]

    # ------------------------------------------------------------------ #
    # Petits utilitaires BeautifulSoup
    # ------------------------------------------------------------------ #
    @staticmethod
    def _soup(html: str):
        try:
            from bs4 import BeautifulSoup  # import paresseux
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "beautifulsoup4 est requis pour LinkedInCrawlerAgent. "
                'Installez l\'extra : pip install -e ".[crawl]"'
            ) from exc
        return BeautifulSoup(html, "html.parser")

    @staticmethod
    def _meta(soup, prop: str) -> str:
        tag = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        )
        return tag.get("content", "").strip() if tag else ""

    @staticmethod
    def _text(soup, selector: str) -> str:
        node = soup.select_one(selector)
        return node.get_text(strip=True) if node else ""
