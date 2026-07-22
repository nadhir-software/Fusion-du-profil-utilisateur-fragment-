"""AmazonCrawlerAgent — collecte d'avis publics via Playwright + BeautifulSoup.

Collecte les avis/notes publics d'un profil public Amazon, les anonymise puis
les stocke dans un silo isolé. Signal ``purchase``.

⚠️ Confidentialité & conformité : seuls des avis **publics** sont collectés et
ils sont anonymisés immédiatement par ``DataAnonymizer`` (via
``CrawlerAgent.run``) AVANT tout stockage. Le texte libre de chaque avis est
placé sous la clé ``text`` afin d'être nettoyé de ses PII résiduels. Respecter
les CGU Amazon et le RGPD reste de la responsabilité de l'utilisateur.

Note : la structure HTML d'Amazon et ses protections anti-bot évoluent ; les
sélecteurs ci-dessous sont best-effort et peuvent nécessiter un ajustement.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from .base_crawler import CrawlerAgent
from .rate_limiter import RateLimiter

# .../profile/amzn1.account.ABC123/ ou ?...&userId=ABC123
_PROFILE_ID_RE = re.compile(r"/(?:profile|gp/profile)/([^/?#]+)")
_RATING_RE = re.compile(r"([0-5](?:[.,]\d)?)\s*(?:out of|sur)\s*5", re.IGNORECASE)


class AmazonCrawlerAgent(CrawlerAgent):
    """Crawler Amazon (Playwright + BeautifulSoup)."""

    platform = "amazon"
    name = "amazon_crawler"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.limit_reviews = self.config.get("limit_reviews", 50)
        self.headless = self.config.get("headless", True)
        self.timeout_ms = self.config.get("timeout_ms", 30_000)
        self.rate_limiter = RateLimiter(
            rate=self.config.get("requests_per_minute", 15), per=60.0
        )

    # ------------------------------------------------------------------ #
    # API publique
    # ------------------------------------------------------------------ #
    def crawl_user(self, identifier: str) -> dict[str, Any]:
        """Collecte les avis publics (produit, catégorie, note, texte).

        Args:
            identifier: URL du profil public Amazon.

        Returns:
            dict ``{"username": profile_id, "reviews": [ {...}, ... ]}``
            NON anonymisé — l'anonymisation est appliquée par :meth:`run`.
        """
        html = self._fetch_html(identifier)
        reviews = self._parse_reviews(html)
        return {
            "username": self._profile_id_from_url(identifier),
            "reviews": reviews[: self.limit_reviews],
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
                "playwright est requis pour AmazonCrawlerAgent. "
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
    def _profile_id_from_url(url: str) -> str:
        """Extrait l'identifiant de profil public depuis l'URL Amazon."""
        match = _PROFILE_ID_RE.search(url)
        if match:
            return match.group(1)
        qs = parse_qs(urlparse(url).query)
        for key in ("userId", "userID", "ie"):
            if key in qs and qs[key]:
                return qs[key][0]
        path = urlparse(url).path.strip("/")
        return path or url

    def _parse_reviews(self, html: str) -> list[dict[str, Any]]:
        """Extrait les avis publics (produit, catégorie, note, texte)."""
        soup = self._soup(html)
        cards = soup.select("[data-hook='review'], .review, .a-section.profile-at-card")
        reviews: list[dict[str, Any]] = []
        for card in cards:
            product = self._text(
                card, "[data-hook='product-link'], .a-link-normal, .product-title"
            )
            body = self._text(
                card, "[data-hook='review-body'], .review-text, .a-expander-content"
            )
            reviews.append(
                {
                    "product": product,
                    "category": self._text(card, "[data-hook='review-category']"),
                    "rating": self._parse_rating(card),
                    "text": body,  # champ libre -> nettoyé par l'anonymiseur
                    "type": "review",
                }
            )
        return reviews

    @classmethod
    def _parse_rating(cls, card) -> float:
        """Extrait la note (0..5) depuis le texte de l'étoile."""
        node = card.select_one(
            "[data-hook='review-star-rating'] span, .a-icon-alt, [class*='star']"
        )
        if not node:
            return 0.0
        match = _RATING_RE.search(node.get_text(" ", strip=True))
        if not match:
            return 0.0
        return float(match.group(1).replace(",", "."))

    # ------------------------------------------------------------------ #
    # Petits utilitaires BeautifulSoup
    # ------------------------------------------------------------------ #
    @staticmethod
    def _soup(html: str):
        try:
            from bs4 import BeautifulSoup  # import paresseux
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "beautifulsoup4 est requis pour AmazonCrawlerAgent. "
                'Installez l\'extra : pip install -e ".[crawl]"'
            ) from exc
        return BeautifulSoup(html, "html.parser")

    @staticmethod
    def _text(node, selector: str) -> str:
        found = node.select_one(selector)
        return found.get_text(" ", strip=True) if found else ""
