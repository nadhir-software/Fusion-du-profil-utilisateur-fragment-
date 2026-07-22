"""ProfileStore — stockage et indexation des profils JSON.

Persiste chaque profil dans ``<profiles_dir>/<user_hash>.json`` et fournit
un chargement individuel ou global. Implémentation par méthodes de classe pour
un usage direct (``ProfileStore.load(user_hash)``) conforme à l'API REST.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_PROFILES_DIR = Path("./data/profiles")


class ProfileStore:
    """Magasin de profils JSON indexés par ``user_hash``."""

    profiles_dir: Path = DEFAULT_PROFILES_DIR

    @classmethod
    def _path(cls, user_hash: str) -> Path:
        return cls.profiles_dir / f"{user_hash}.json"

    @classmethod
    def save(cls, profile: dict[str, Any]) -> Path:
        """Persiste un profil ; requiert la clé ``user_hash``."""
        user_hash = profile["user_hash"]
        path = cls._path(user_hash)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    @classmethod
    def load(cls, user_hash: str) -> dict[str, Any] | None:
        """Charge un profil, ou ``None`` s'il n'existe pas."""
        path = cls._path(user_hash)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def load_all(cls) -> list[dict[str, Any]]:
        """Charge tous les profils du magasin."""
        if not cls.profiles_dir.exists():
            return []
        return [
            json.loads(p.read_text(encoding="utf-8"))
            for p in cls.profiles_dir.glob("*.json")
        ]
