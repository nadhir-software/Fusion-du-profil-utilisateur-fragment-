"""Interface abstraite commune à tous les agents du système.

Chaque agent (crawler, preprocessor, trainer, ...) hérite de BaseAgent et
implémente `run(**kwargs)`. `validate_output` fournit un garde-fou générique
pour vérifier la forme du résultat avant qu'il ne soit propagé.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Classe de base pour tous les agents.

    Sous-classes attendues : RedditCrawlerAgent, LinkedInCrawlerAgent,
    AmazonCrawlerAgent, PreprocessorAgent, TrainerAgent, ...
    """

    #: identifiant lisible de l'agent (surchargé par les sous-classes).
    name: str = "base_agent"

    @abstractmethod
    def run(self, **kwargs: Any) -> dict:
        """Exécute la tâche de l'agent et renvoie un dictionnaire de résultat.

        Doit être implémentée par chaque sous-classe.
        """
        raise NotImplementedError

    def validate_output(self, output: Any) -> bool:
        """Valide la forme minimale d'une sortie d'agent.

        Par défaut : un dictionnaire contenant une clé ``status``.
        Les sous-classes peuvent renforcer cette validation.
        """
        return isinstance(output, dict) and "status" in output

    def __repr__(self) -> str:  # pragma: no cover - cosmétique
        return f"<{type(self).__name__} name={self.name!r}>"
