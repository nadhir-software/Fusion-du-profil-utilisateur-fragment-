"""ProfileStore — magasin de profils, backend RAM enfichable.

Deux backends, **aucun n'écrit sur disque** (principe « ne pas enregistrer les
data ») :

- ``memory`` (défaut) : registre en RAM local au process. Simple, mais non
  partagé entre process/workers et volatil au redémarrage.
- ``redis``  : Redis en mode **RAM-only** (persistance désactivée côté serveur,
  cf. RUNBOOK). Partagé entre le CLI, l'API et plusieurs workers uvicorn.

Sélection par variable d'environnement :

    PROFILE_STORE_BACKEND = "memory" | "redis"   (défaut : "memory")
    REDIS_URL             = "redis://localhost:6379/0"

``ProfileStore`` est une **façade** : ses méthodes de classe délèguent au
backend configuré. Tous les appelants existants (``ProfileStore.save`` /
``load`` / ``load_all`` / ``clear``) fonctionnent sans changement.
"""

from __future__ import annotations

import json
import os
from typing import Any, Protocol


class _Backend(Protocol):
    def save(self, profile: dict[str, Any]) -> str: ...
    def load(self, user_hash: str) -> dict[str, Any] | None: ...
    def load_all(self) -> list[dict[str, Any]]: ...
    def clear(self) -> None: ...


class InMemoryProfileBackend:
    """Registre de profils en RAM, local au process."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def save(self, profile: dict[str, Any]) -> str:
        user_hash = profile["user_hash"]
        self._store[user_hash] = profile
        return user_hash

    def load(self, user_hash: str) -> dict[str, Any] | None:
        return self._store.get(user_hash)

    def load_all(self) -> list[dict[str, Any]]:
        return list(self._store.values())

    def clear(self) -> None:
        self._store.clear()


class RedisProfileBackend:
    """Backend Redis (RAM-only) partagé entre process.

    Le client peut être injecté (tests) ; sinon un client redis est créé à
    partir de l'URL. ⚠️ Le serveur Redis doit tourner **sans persistance**
    (``redis-server --save "" --appendonly no``) pour respecter le « no disk ».
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        prefix: str = "profile:",
        client: Any | None = None,
    ) -> None:
        self.prefix = prefix
        if client is not None:
            self.client = client
        else:
            try:
                import redis  # import paresseux (dépendance optionnelle)
            except ImportError as exc:  # pragma: no cover
                raise ImportError(
                    "redis est requis pour RedisProfileBackend. "
                    'Installez : pip install -e ".[redis]"'
                ) from exc
            self.client = redis.Redis.from_url(url, decode_responses=True)

    def _key(self, user_hash: str) -> str:
        return f"{self.prefix}{user_hash}"

    def save(self, profile: dict[str, Any]) -> str:
        user_hash = profile["user_hash"]
        self.client.set(self._key(user_hash), json.dumps(profile, ensure_ascii=False))
        return user_hash

    def load(self, user_hash: str) -> dict[str, Any] | None:
        raw = self.client.get(self._key(user_hash))
        return json.loads(raw) if raw else None

    def load_all(self) -> list[dict[str, Any]]:
        keys = list(self.client.keys(f"{self.prefix}*"))
        if not keys:
            return []
        return [json.loads(v) for v in self.client.mget(keys) if v]

    def clear(self) -> None:
        keys = list(self.client.keys(f"{self.prefix}*"))
        if keys:
            self.client.delete(*keys)


def _make_backend() -> _Backend:
    backend = os.getenv("PROFILE_STORE_BACKEND", "memory").lower()
    if backend == "redis":
        return RedisProfileBackend(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    return InMemoryProfileBackend()


class ProfileStore:
    """Façade : délègue au backend configuré (mémoire ou Redis)."""

    _backend: _Backend | None = None

    @classmethod
    def backend(cls) -> _Backend:
        if cls._backend is None:
            cls._backend = _make_backend()
        return cls._backend

    @classmethod
    def set_backend(cls, backend: _Backend | None) -> None:
        """Force un backend (utile pour les tests) ; None => re-sélection."""
        cls._backend = backend

    @classmethod
    def save(cls, profile: dict[str, Any]) -> str:
        return cls.backend().save(profile)

    @classmethod
    def load(cls, user_hash: str) -> dict[str, Any] | None:
        return cls.backend().load(user_hash)

    @classmethod
    def load_all(cls) -> list[dict[str, Any]]:
        return cls.backend().load_all()

    @classmethod
    def clear(cls) -> None:
        cls.backend().clear()
