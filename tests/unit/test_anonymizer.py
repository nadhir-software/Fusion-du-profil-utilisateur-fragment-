"""Tests CRITIQUES — invariant de confidentialité de DataAnonymizer."""

from maha_these.core.anonymizer import DataAnonymizer


def test_anonymizer_no_pii():
    """Aucun PII ne doit survivre à l'anonymisation."""
    anon = DataAnonymizer()
    raw = {
        "username": "john_doe_123",
        "posts": [{"body": "Contact me at john@email.com via u/john_doe_123"}],
    }
    result = anon.anonymize(raw)
    result_str = str(result)

    assert "john_doe_123" not in result_str
    assert "john@email.com" not in result_str
    assert "user_hash" in result


def test_hash_deterministic():
    """Le hash d'un identifiant est déterministe et de longueur fixe."""
    anon = DataAnonymizer()
    h1 = anon.hash_id("alice")
    h2 = anon.hash_id("alice")
    assert h1 == h2
    assert len(h1) == 32
    assert anon.hash_id("alice") != anon.hash_id("bob")


def test_clean_text_removes_mentions_urls_emails():
    anon = DataAnonymizer()
    cleaned = anon.clean_text(
        "hi u/bob see https://x.com and mail me a@b.com"
    )
    assert "u/bob" not in cleaned
    assert "https://x.com" not in cleaned
    assert "a@b.com" not in cleaned
    assert "[USER]" in cleaned
    assert "[URL]" in cleaned
    assert "[EMAIL]" in cleaned
