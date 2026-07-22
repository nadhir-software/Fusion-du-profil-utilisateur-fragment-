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
