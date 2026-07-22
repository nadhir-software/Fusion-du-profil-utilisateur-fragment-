"""Tests ProfileStore — backends RAM (mémoire + Redis via faux client)."""

import pytest

from maha_these.layer3_profile.profile_store import (
    InMemoryProfileBackend,
    ProfileStore,
    RedisProfileBackend,
    _make_backend,
)


@pytest.fixture(autouse=True)
def _reset_backend():
    """Réinitialise le backend de la façade après chaque test."""
    yield
    ProfileStore.set_backend(None)


class _FakeRedis:
    """Client Redis minimal en mémoire (set/get/keys/mget/delete)."""

    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def keys(self, pattern):
        prefix = pattern.rstrip("*")
        return [k for k in self.data if k.startswith(prefix)]

    def mget(self, keys):
        return [self.data.get(k) for k in keys]

    def delete(self, *keys):
        for k in keys:
            self.data.pop(k, None)


PROFILE = {"user_hash": "abc", "interests": ["ml"], "marketing_segments": ["x"]}


def test_in_memory_backend_roundtrip():
    b = InMemoryProfileBackend()
    assert b.save(PROFILE) == "abc"
    assert b.load("abc")["interests"] == ["ml"]
    assert b.load("missing") is None
    assert len(b.load_all()) == 1
    b.clear()
    assert b.load_all() == []


def test_redis_backend_roundtrip_with_fake_client():
    b = RedisProfileBackend(client=_FakeRedis())
    assert b.save(PROFILE) == "abc"
    assert b.load("abc")["marketing_segments"] == ["x"]  # (dé)sérialisation JSON
    assert b.load("missing") is None
    assert len(b.load_all()) == 1
    b.clear()
    assert b.load_all() == []


def test_redis_backend_isolation_by_prefix():
    fake = _FakeRedis()
    fake.set("other:key", "not a profile")  # clé hors préfixe
    b = RedisProfileBackend(client=fake, prefix="profile:")
    b.save(PROFILE)
    assert len(b.load_all()) == 1  # ignore la clé "other:key"
    b.clear()
    assert fake.get("other:key") == "not a profile"  # non touchée


def test_default_backend_is_memory(monkeypatch):
    monkeypatch.delenv("PROFILE_STORE_BACKEND", raising=False)
    assert isinstance(_make_backend(), InMemoryProfileBackend)


def test_facade_delegates_to_configured_backend():
    ProfileStore.set_backend(RedisProfileBackend(client=_FakeRedis()))
    ProfileStore.save(PROFILE)
    assert ProfileStore.load("abc")["interests"] == ["ml"]
    assert len(ProfileStore.load_all()) == 1
    ProfileStore.clear()
    assert ProfileStore.load_all() == []
