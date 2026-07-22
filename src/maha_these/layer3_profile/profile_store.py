"""ProfileStore — magasin de profils EN MÉMOIRE (RAM uniquement).

Conformément au principe fondateur (« ne pas enregistrer les data »), les
profils générés ne sont **jamais** écrits sur disque : ils sont conservés dans
un registre en RAM, indexé par ``user_hash``, partagé au sein du processus API.

Conséquence assumée : les profils sont volatils (perdus au redémarrage du
processus) et non partagés entre workers. C'est le compromis voulu pour
garantir l'absence totale de persistance. Pour un déploiement multi-workers,
brancher un magasin externe chiffré resterait une extension (hors périmètre).
"""

from __future__ import annotations

from typing import Any


class ProfileStore:
    """Registre de profils en mémoire, indexé par ``user_hash``."""

    #: registre RAM partagé au niveau du processus.
    _store: dict[str, dict[str, Any]] = {}

    @classmethod
    def save(cls, profile: dict[str, Any]) -> str:
        """Enregistre un profil en RAM ; requiert la clé ``user_hash``."""
        user_hash = profile["user_hash"]
        cls._store[user_hash] = profile
        return user_hash

    @classmethod
    def load(cls, user_hash: str) -> dict[str, Any] | None:
        """Charge un profil, ou ``None`` s'il n'existe pas."""
        return cls._store.get(user_hash)

    @classmethod
    def load_all(cls) -> list[dict[str, Any]]:
        """Charge tous les profils du registre."""
        return list(cls._store.values())

    @classmethod
    def clear(cls) -> None:
        """Vide le registre (effacement RAM explicite)."""
        cls._store.clear()
