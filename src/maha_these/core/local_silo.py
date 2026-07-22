"""LocalDataSilo — stockage local isolé par plateforme.

Chaque silo est physiquement séparé (un sous-dossier par plateforme et par
``user_hash``). L'isolation stricte garantit qu'un agent ne peut lire que son
propre silo — invariant vérifié par tests/unit/test_silo_isolation.py.

Les données ne quittent JAMAIS le silo : seuls les poids LoRA (Δθ) issus de
l'entraînement local sont exportés vers l'agrégateur fédéré.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalDataSilo:
    """Silo de données local, isolé par ``(platform, user_hash)``."""

    def __init__(
        self,
        platform: str,
        data: dict[str, Any] | None = None,
        output_dir: str | Path = "./data/silos",
    ) -> None:
        self.platform = platform
        self.data = data or {}
        self.output_dir = Path(output_dir)
        self.user_hash = str(self.data.get("user_hash", "anonymous"))

    @property
    def path(self) -> Path:
        """Chemin isolé : ``<output_dir>/<platform>/<user_hash>.json``."""
        return self.output_dir / self.platform / f"{self.user_hash}.json"

    def save(self) -> Path:
        """Écrit les données anonymisées sur disque et renvoie le chemin."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.path

    def load(self) -> dict[str, Any]:
        """Recharge les données du silo depuis le disque."""
        if not self.path.exists():
            raise FileNotFoundError(f"Silo introuvable : {self.path}")
        return json.loads(self.path.read_text(encoding="utf-8"))

    def can_read(self, other_path: str | Path) -> bool:
        """Isolation stricte : un silo ne peut lire que son propre chemin.

        Renvoie False pour tout chemin n'appartenant pas à ce silo.
        """
        return Path(other_path).resolve() == self.path.resolve()

    def __repr__(self) -> str:  # pragma: no cover - cosmétique
        return (
            f"<LocalDataSilo platform={self.platform!r} user_hash={self.user_hash!r}>"
        )
