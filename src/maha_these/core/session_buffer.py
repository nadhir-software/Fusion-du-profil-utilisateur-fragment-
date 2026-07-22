"""SessionBuffer — tampon de données EN MÉMOIRE (RAM uniquement).

Principe fondateur du projet : **ne jamais enregistrer les données**.
Aucune écriture disque n'est effectuée ici — ni base de données, ni CSV, ni
JSON, ni cache. Les données (brutes anonymisées puis prétraitées) transitent
uniquement en RAM et sont effacées explicitement en fin de session.

Isolation :
- **par session** : deux sessions ne partagent aucune donnée (registre isolé).
- **par plateforme** : au sein d'une session, chaque plateforme dispose d'un
  compartiment séparé ; un agent n'accède qu'au sien.

Usage recommandé (garantit l'effacement, même en cas d'exception) ::

    with SessionBuffer() as buf:
        buf.write("reddit", anon_data)
        data = buf.read("reddit")
    # à la sortie du bloc, buf est vidé : plus aucune donnée en mémoire.
"""

from __future__ import annotations

import uuid
from types import TracebackType
from typing import Any, Iterator


class SessionBuffer:
    """Tampon RAM isolé par session ; aucune persistance disque."""

    #: registre en mémoire des buffers vivants, pour vérifier l'isolation.
    _registry: dict[str, "SessionBuffer"] = {}

    def __init__(self, session_id: str | None = None) -> None:
        self.session_id = session_id or uuid.uuid4().hex
        # compartiment par plateforme : {platform: {donnees anonymisées}}
        self._store: dict[str, dict[str, Any]] = {}
        SessionBuffer._registry[self.session_id] = self

    # ------------------------------------------------------------------ #
    # Écriture / lecture (RAM seulement)
    # ------------------------------------------------------------------ #
    def write(self, platform: str, data: dict[str, Any]) -> None:
        """Stocke des données anonymisées en RAM pour une plateforme."""
        self._store[platform] = data

    def read(self, platform: str) -> dict[str, Any] | None:
        """Lit le compartiment d'une plateforme (ou None si absent)."""
        return self._store.get(platform)

    def platforms(self) -> list[str]:
        """Liste des plateformes présentes dans la session."""
        return list(self._store.keys())

    def items(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Itère sur ``(platform, data)`` — utile pour le prétraitement."""
        yield from self._store.items()

    # ------------------------------------------------------------------ #
    # Isolation & cycle de vie
    # ------------------------------------------------------------------ #
    def can_access(self, other: "SessionBuffer") -> bool:
        """Isolation stricte : un buffer n'accède qu'à sa propre session."""
        return other.session_id == self.session_id

    def clear(self) -> None:
        """Efface toutes les données de la session (RAM wipe explicite)."""
        self._store.clear()
        SessionBuffer._registry.pop(self.session_id, None)

    @classmethod
    def get(cls, session_id: str) -> "SessionBuffer | None":
        """Récupère un buffer vivant par son identifiant de session."""
        return cls._registry.get(session_id)

    # ------------------------------------------------------------------ #
    # Context manager — garantit l'effacement en fin de bloc
    # ------------------------------------------------------------------ #
    def __enter__(self) -> "SessionBuffer":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.clear()

    def __repr__(self) -> str:  # pragma: no cover - cosmétique
        return (
            f"<SessionBuffer session={self.session_id[:8]} "
            f"platforms={self.platforms()}>"
        )
