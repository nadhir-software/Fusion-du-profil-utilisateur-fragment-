"""Tests LinkedInCrawlerAgent — parsing (offline) + flux anonymisé en RAM.

Aucune I/O réseau : le HTML est fourni en dur et ``crawl_user`` est
monkeypatché pour valider l'anonymisation appliquée par ``run()`` — laquelle
n'écrit QUE dans un tampon mémoire (SessionBuffer), jamais sur disque.
"""

import json

import pytest

from maha_these.core.session_buffer import SessionBuffer
from maha_these.layer1_crawling.linkedin_crawler import LinkedInCrawlerAgent

SAMPLE_HTML = """
<html><head>
<meta property="og:title" content="Jane Doe - Data Scientist at ACME"/>
<meta property="og:description" content="ML engineer. Reach me at jane@acme.com"/>
</head><body>
<h1>Jane Doe</h1>
<section id="skills">
  <li><span aria-hidden="true">Python</span></li>
  <li><span aria-hidden="true">PyTorch</span></li>
</section>
</body></html>
"""


def test_handle_from_url():
    c = LinkedInCrawlerAgent()
    assert c._handle_from_url("https://www.linkedin.com/in/john-doe/") == "john-doe"
    assert c._handle_from_url("https://www.linkedin.com/in/jane?trk=x") == "jane"
    assert c._handle_from_url("https://example.com/profile/x") == "profile/x"


def test_parse_profile_and_skills():
    pytest.importorskip("bs4")
    c = LinkedInCrawlerAgent()

    profile = c._parse_profile(SAMPLE_HTML)
    assert "Jane Doe" in profile["headline"]
    # brut ici (le nettoyage PII a lieu dans run() via l'anonymiseur)
    assert "jane@acme.com" in profile["text"]

    names = {s["name"] for s in c._parse_skills(SAMPLE_HTML)}
    assert {"Python", "PyTorch"} <= names


def test_run_anonymizes_in_ram(monkeypatch):
    """run() doit anonymiser et n'écrire QUE dans le tampon RAM."""
    c = LinkedInCrawlerAgent()
    monkeypatch.setattr(
        c,
        "crawl_user",
        lambda identifier: {
            "username": "jane-doe",
            "profile": [
                {
                    "headline": "Data Scientist",
                    "text": "mail jane@acme.com",
                    "location": "Sfax",
                }
            ],
            "skills": [{"name": "Python"}],
        },
    )

    with SessionBuffer() as buf:
        result = c.run("https://www.linkedin.com/in/jane-doe/", buffer=buf)
        assert result["status"] == "success"
        assert "silo_path" not in result  # rien n'est persisté sur disque

        stored = buf.read("linkedin")
        blob = json.dumps(stored)
        assert "jane-doe" not in blob  # username hashé
        assert "jane@acme.com" not in blob  # email nettoyé
        assert stored["user_hash"] == result["user_hash"]

    # à la sortie du bloc, la session est vidée
    assert buf.read("linkedin") is None
