"""Tests — endpoints de l'API REST (statuts, 404 profil manquant)."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from maha_these.layer3_profile.profile_store import ProfileStore  # noqa: E402
from maha_these.layer5_api.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_store():
    """Registre RAM vidé avant et après chaque test."""
    ProfileStore.clear()
    yield
    ProfileStore.clear()


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_profile_missing_returns_404():
    resp = client.get("/api/v1/profile/does_not_exist")
    assert resp.status_code == 404


def test_get_profile_found():
    ProfileStore.save({"user_hash": "abc", "interests": ["ml"]})
    resp = client.get("/api/v1/profile/abc")
    assert resp.status_code == 200
    assert resp.json()["user_hash"] == "abc"


def test_segments_empty():
    resp = client.get("/api/v1/profiles/segments")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_profiles"] == 0
    assert body["segments"] == []


def test_list_profiles_empty():
    resp = client.get("/api/v1/profiles")
    assert resp.status_code == 200
    assert resp.json() == {"count": 0, "profiles": []}


def test_list_profiles_summary():
    ProfileStore.save(
        {
            "user_hash": "u1",
            "interests": ["ml", "cyclisme", "photo", "cuisine", "extra"],
            "professional": {"sector": "Tech"},
            "marketing_segments": ["a", "b", "c"],
            "platforms_covered": ["reddit"],
        }
    )
    body = client.get("/api/v1/profiles").json()
    assert body["count"] == 1
    p = body["profiles"][0]
    assert p["user_hash"] == "u1"
    assert p["sector"] == "Tech"
    assert len(p["interests"]) == 4  # résumé tronqué
    assert len(p["segments"]) == 2


def test_seed_demo_populates_many_named_profiles():
    resp = client.post("/api/v1/dev/seed")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 16  # profils démo étendus
    hashes = {p["user_hash"] for p in client.get("/api/v1/profiles").json()["profiles"]}
    assert {"demo_alice", "demo_maha", "demo_karim"} <= hashes
