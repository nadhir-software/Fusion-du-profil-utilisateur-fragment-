"""Tests AmazonCrawlerAgent — parsing (offline) + flux anonymisé en RAM.

Aucune I/O réseau : le HTML est fourni en dur et ``crawl_user`` est
monkeypatché pour valider l'anonymisation appliquée par ``run()`` — laquelle
n'écrit QUE dans un tampon mémoire (SessionBuffer), jamais sur disque.
"""

import json

import pytest

from maha_these.core.session_buffer import SessionBuffer
from maha_these.layer1_crawling.amazon_crawler import AmazonCrawlerAgent

SAMPLE_HTML = """
<html><body>
<div data-hook="review">
  <a data-hook="product-link">Wireless Headphones</a>
  <i data-hook="review-star-rating"><span class="a-icon-alt">4.0 out of 5 stars</span></i>
  <span data-hook="review-body">Great sound. Contact seller at bob@shop.com</span>
</div>
<div data-hook="review">
  <a data-hook="product-link">USB-C Cable</a>
  <i data-hook="review-star-rating"><span class="a-icon-alt">5.0 out of 5 stars</span></i>
  <span data-hook="review-body">Works perfectly.</span>
</div>
</body></html>
"""


def test_profile_id_from_url():
    c = AmazonCrawlerAgent()
    assert (
        c._profile_id_from_url(
            "https://www.amazon.com/gp/profile/amzn1.account.ABC123/"
        )
        == "amzn1.account.ABC123"
    )
    assert (
        c._profile_id_from_url("https://www.amazon.com/profile/amzn1.account.XYZ")
        == "amzn1.account.XYZ"
    )
    assert (
        c._profile_id_from_url("https://www.amazon.com/review?userId=USER99")
        == "USER99"
    )
    assert c._profile_id_from_url("https://example.com/foo") == "foo"


def test_parse_reviews():
    pytest.importorskip("bs4")
    c = AmazonCrawlerAgent()
    reviews = c._parse_reviews(SAMPLE_HTML)

    assert len(reviews) == 2
    assert reviews[0]["product"] == "Wireless Headphones"
    assert reviews[0]["rating"] == 4.0
    assert "bob@shop.com" in reviews[0]["text"]  # brut ; nettoyé en aval
    assert reviews[1]["rating"] == 5.0


def test_limit_reviews():
    pytest.importorskip("bs4")
    c = AmazonCrawlerAgent(config={"limit_reviews": 1})
    c._fetch_html = lambda url: SAMPLE_HTML  # type: ignore[assignment]
    out = c.crawl_user("https://www.amazon.com/profile/amzn1.account.XYZ")
    assert len(out["reviews"]) == 1


def test_run_anonymizes_in_ram(monkeypatch):
    """run() doit anonymiser et n'écrire QUE dans le tampon RAM."""
    c = AmazonCrawlerAgent()
    monkeypatch.setattr(
        c,
        "crawl_user",
        lambda identifier: {
            "username": "amzn1.account.XYZ",
            "reviews": [
                {
                    "product": "P",
                    "text": "mail bob@shop.com",
                    "rating": 4.0,
                    "type": "review",
                }
            ],
        },
    )

    with SessionBuffer() as buf:
        result = c.run("https://www.amazon.com/profile/amzn1.account.XYZ", buffer=buf)
        assert result["status"] == "success"
        assert "silo_path" not in result  # rien n'est persisté sur disque

        stored = buf.read("amazon")
        blob = json.dumps(stored)
        assert "amzn1.account.XYZ" not in blob  # identifiant hashé
        assert "bob@shop.com" not in blob  # email nettoyé
        assert stored["user_hash"] == result["user_hash"]

    assert buf.read("amazon") is None  # session vidée
