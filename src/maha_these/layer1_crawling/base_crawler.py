"""CrawlerAgent — classe abstraite commune aux crawlers de plateformes.

Impose le contrat : chaque crawler collecte des données publiques, les fait
passer par ``DataAnonymizer`` puis les pousse dans un ``SessionBuffer``
**en mémoire (RAM)**. Aucune donnée n'est jamais écrite sur disque — principe
fondateur du projet (« ne pas enregistrer les data »). Seuls les Δθ (poids
LoRA) issus de l'entraînement local quitteront ensuite la session.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from maha_these.core.anonymizer import DataAnonymizer
from maha_these.core.base_agent import BaseAgent
from maha_these.core.session_buffer import SessionBuffer


class CrawlerAgent(BaseAgent):
    """Base des agents de collecte multi-plateformes (streaming RAM only)."""

    #: nom de la plateforme (surchargé : "reddit", "linkedin", "amazon").
    platform: str = "generic"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.anonymizer = DataAnonymizer()

    @abstractmethod
    def crawl_user(self, identifier: str) -> dict[str, Any]:
        """Collecte les données publiques brutes d'un utilisateur.

        Renvoie un dict ``{"username": ..., <collections>}`` NON anonymisé ;
        l'anonymisation est appliquée par :meth:`run`.
        """
        raise NotImplementedError

    def run(
        self,
        identifier: str,
        buffer: SessionBuffer | None = None,
    ) -> dict[str, Any]:
        """Collecte -> anonymise -> pousse en RAM (SessionBuffer).

        Args:
            identifier: identifiant/URL de l'utilisateur sur la plateforme.
            buffer: tampon mémoire partagé (fourni par l'orchestrateur). Si
                ``None``, un buffer éphémère est créé pour cette collecte.

        Returns:
            Métadonnées de collecte — **jamais** de chemin disque, puisque
            rien n'est persisté.
        """
        buf = buffer or SessionBuffer()
        raw_data = self.crawl_user(identifier)
        anon_data = self.anonymizer.anonymize(raw_data)  # AVANT tout traitement
        buf.write(self.platform, anon_data)  # RAM uniquement

        n_items = sum(len(v) for v in anon_data.values() if isinstance(v, list))
        return {
            "status": "success",
            "platform": self.platform,
            "session_id": buf.session_id,
            "user_hash": anon_data["user_hash"],
            "n_items": n_items,
        }
