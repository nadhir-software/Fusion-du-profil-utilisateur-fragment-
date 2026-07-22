"""OrchestrationAgent — Workflow Manager & Task Scheduler.

Sommet de l'architecture : reçoit une requête utilisateur, planifie les
crawlers de plateformes vers **un seul** ``SessionBuffer`` en RAM, puis pilote
le cycle de vie de la session (collecte -> prétraitement -> ... -> effacement).

Garantie « ne pas enregistrer les data » : la session vit en mémoire et est
vidée à la fin (context manager). L'orchestrateur ne dépend que d'abstractions
(``BaseAgent``, ``SessionBuffer``) — les crawlers concrets sont injectés par la
couche appelante (API), évitant toute inversion de dépendance.
"""

from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent
from .session_buffer import SessionBuffer


class OrchestrationAgent(BaseAgent):
    """Planifie et coordonne les agents de collecte sur une session RAM."""

    name = "orchestrator"

    def __init__(self, crawlers: dict[str, BaseAgent] | None = None) -> None:
        #: {platform: crawler-like agent}, ex. {"reddit": RedditCrawlerAgent()}
        self.crawlers = crawlers or {}

    def register(self, platform: str, crawler: BaseAgent) -> None:
        """Enregistre un crawler pour une plateforme."""
        self.crawlers[platform] = crawler

    def collect(
        self, targets: dict[str, str], session_id: str | None = None
    ) -> SessionBuffer:
        """Lance chaque crawler enregistré vers sa cible, dans UN buffer RAM.

        Args:
            targets: ``{platform: identifier}`` (identifier vide -> ignoré).
            session_id: identifiant de session optionnel.

        Returns:
            Le ``SessionBuffer`` (RAM) peuplé. L'appelant est responsable de
            son effacement — préférer :meth:`run` qui le garantit.
        """
        buf = SessionBuffer(session_id)
        for platform, identifier in targets.items():
            crawler = self.crawlers.get(platform)
            if crawler is None or not identifier:
                continue
            crawler.run(identifier, buffer=buf)  # écrit en RAM dans `buf`
        return buf

    def run(self, targets: dict[str, str], **kwargs: Any) -> dict[str, Any]:
        """Session complète : collecte en RAM, résumé, puis effacement.

        Le buffer est vidé à la sortie du bloc ``with`` : aucune donnée ne
        subsiste. Ne renvoie que des métadonnées non sensibles.
        """
        with self.collect(targets, kwargs.get("session_id")) as buf:
            summary = {
                "status": "success",
                "session_id": buf.session_id,
                "platforms_collected": buf.platforms(),
                "user_hashes": {
                    platform: data.get("user_hash") for platform, data in buf.items()
                },
            }
            # TODO(Phase 1/2): enchaîner ici prétraitement -> fragments ->
            #   entraînement local (Δθ) -> agrégation, tant que `buf` est vivant.
        return summary
