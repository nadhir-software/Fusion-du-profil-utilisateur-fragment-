"""CrawlerAgent — classe abstraite commune aux crawlers de plateformes.

Impose le contrat : chaque crawler collecte des données publiques, les fait
passer par ``DataAnonymizer`` puis les persiste dans un ``LocalDataSilo``
isolé. La donnée brute (nominative) ne doit jamais atteindre le disque.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from maha_these.core.anonymizer import DataAnonymizer
from maha_these.core.base_agent import BaseAgent
from maha_these.core.local_silo import LocalDataSilo


class CrawlerAgent(BaseAgent):
    """Base des agents de collecte multi-plateformes."""

    #: nom de la plateforme (surchargé : "reddit", "linkedin", "amazon").
    platform: str = "generic"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.anonymizer = DataAnonymizer()
        self.output_dir = self.config.get("output_dir", "./data/silos")

    @abstractmethod
    def crawl_user(self, identifier: str) -> dict[str, Any]:
        """Collecte les données publiques brutes d'un utilisateur.

        Renvoie un dict ``{"username": ..., <collections>}`` NON anonymisé ;
        l'anonymisation est appliquée par :meth:`run`.
        """
        raise NotImplementedError

    def run(self, identifier: str, output_dir: str | None = None) -> dict[str, Any]:
        """Collecte -> anonymise -> stocke dans un silo local isolé."""
        raw_data = self.crawl_user(identifier)
        anon_data = self.anonymizer.anonymize(raw_data)  # AVANT tout stockage
        silo = LocalDataSilo(
            platform=self.platform,
            data=anon_data,
            output_dir=output_dir or self.output_dir,
        )
        path = silo.save()
        n_items = sum(len(v) for v in anon_data.values() if isinstance(v, list))
        return {
            "status": "success",
            "platform": self.platform,
            "silo_path": str(path),
            "user_hash": anon_data["user_hash"],
            "n_items": n_items,
        }
