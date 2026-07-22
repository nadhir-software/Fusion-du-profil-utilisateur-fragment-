"""Configurations de référence pour la comparaison scientifique.

Trois configs, mêmes données / même modèle / même seed :
- FederatedConfig    : système proposé (Trainer×N + FedAvg).
- CentralizedConfig  : baseline haute (Trainer×1, données fusionnées).
- MonoSourceConfig   : baseline basse (Trainer×1, une seule plateforme).

Chaque config expose ``run_pipeline(data) -> profile`` afin d'être comparée
sur un pied d'égalité par l'EvaluationRunner. La logique d'entraînement réelle
est branchée en Phase 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseConfig:
    """Contrat commun aux trois configurations comparées."""

    name: str = "base"
    seed: int = 42
    base_model: str = "mistralai/Mistral-7B-Instruct-v0.3"
    extra: dict[str, Any] = field(default_factory=dict)

    def run_pipeline(self, data: Any) -> dict[str, Any]:
        """Exécute le pipeline propre à la config et renvoie un profil."""
        raise NotImplementedError(
            f"{type(self).__name__}.run_pipeline() à implémenter (Phase 3)."
        )


@dataclass
class FederatedConfig(BaseConfig):
    """Config A — système fédéré proposé (Trainer×N + FedAvg)."""

    name: str = "federated"
    algorithm: str = "fedavg"
    n_fragments: int = 3


@dataclass
class CentralizedConfig(BaseConfig):
    """Config B — baseline haute : données fusionnées, un seul trainer."""

    name: str = "centralized"


@dataclass
class MonoSourceConfig(BaseConfig):
    """Config C — baseline basse : une seule plateforme (Reddit F1)."""

    name: str = "mono_source"
    source: str = "F1_reddit"
