"""Baselines pour la comparaison scientifique (EXP-01).

Trois configurations — **mêmes données, même modèle, même seed** — qui ne
diffèrent QUE par leur **plan de fragmentation** :

- ``FederatedConfig``   : un fragment par plateforme + FedAvg (système proposé).
- ``CentralizedConfig`` : un unique fragment, données fusionnées (baseline haute).
- ``MonoSourceConfig``  : un seul fragment, une plateforme (baseline basse).

``fragment_plan()`` est **pur Python et testé**. ``run_pipeline()`` enchaîne
fragment → train → agrégation → génération de profil ; les étapes ML sont en
import paresseux (surchargeables pour les tests).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from maha_these.layer2_federated.fragment_builder import FragmentBuilder
from maha_these.layer2_federated.lora_config import DEFAULT_LORA_CFG
from maha_these.layer2_federated.system_prompts import SYSTEM_PROMPTS
from maha_these.layer2_federated.trainer_agent import TrainerAgent
from maha_these.layer3_profile.aggregator import FederatedAggregator
from maha_these.layer3_profile.profile_generator import ProfileGenerator
from maha_these.pipeline import PLATFORM_FRAGMENTS, load_global_model

SIGNAL_BY_FRAGMENT = {fid: sig for fid, sig in PLATFORM_FRAGMENTS.values()}


@dataclass
class BaselineConfig:
    """Contrat commun aux configurations comparées."""

    name: str = "base"
    lora_cfg: dict = field(default_factory=lambda: dict(DEFAULT_LORA_CFG))
    training_cfg: dict = field(default_factory=dict)
    fed_cfg: dict = field(default_factory=dict)

    def fragment_plan(
        self, platform_texts: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """Renvoie ``{fragment_id: textes}`` — spécifique à chaque config."""
        raise NotImplementedError

    def run_pipeline(
        self, platform_texts: dict[str, list[str]], user_hash: str = "exp_user"
    ) -> dict:
        """Fragmente → entraîne → agrège → génère le profil."""
        plan = self.fragment_plan(platform_texts)
        outputs = [
            self._train(fid, texts, user_hash) for fid, texts in plan.items() if texts
        ]
        if not outputs:
            return {"user_hash": user_hash, "interests": [], "error": "no_data"}
        theta = self._aggregate(outputs)
        return self._generate(theta, user_hash)

    # -- hooks ML (import paresseux, surchargeables pour les tests) -------- #
    def _train(self, fragment_id: str, texts: list[str], user_hash: str):
        signal = SIGNAL_BY_FRAGMENT.get(fragment_id, "interest")
        dataset, _ = FragmentBuilder(fragment_id, signal).build(texts, user_hash)
        trainer = TrainerAgent(
            fragment_id,
            SYSTEM_PROMPTS.get(fragment_id, ""),
            self.lora_cfg,
            self.training_cfg.get("base_model", "mistralai/Mistral-7B-Instruct-v0.3"),
            self.training_cfg,
        )
        return trainer.run(dataset, global_weights=None)

    def _aggregate(self, outputs) -> dict:
        aggregator = FederatedAggregator(
            self.fed_cfg.get("algorithm", "fedavg"), self.fed_cfg.get("mu", 0.01)
        )
        theta = aggregator.aggregate(outputs)
        sigma = self.fed_cfg.get("dp_noise_sigma", 0.0)
        if sigma and sigma > 0:  # Differential Privacy optionnelle (EXP-05)
            theta = aggregator.add_dp_noise(theta, sigma)
        return theta

    def _generate(self, theta: dict, user_hash: str) -> dict:
        model, tokenizer = load_global_model(theta, self.lora_cfg, self.training_cfg)
        return ProfileGenerator().generate(model, tokenizer, user_hash)


@dataclass
class FederatedConfig(BaselineConfig):
    """Config A — un fragment par plateforme + FedAvg (système proposé)."""

    name: str = "federated"

    def fragment_plan(self, platform_texts):
        return {
            PLATFORM_FRAGMENTS.get(p, (f"F_{p}", "interest"))[0]: texts
            for p, texts in platform_texts.items()
        }


@dataclass
class CentralizedConfig(BaselineConfig):
    """Config B — un unique fragment, données fusionnées (baseline haute)."""

    name: str = "centralized"

    def fragment_plan(self, platform_texts):
        merged = [t for texts in platform_texts.values() for t in texts]
        return {"F_central": merged}


@dataclass
class MonoSourceConfig(BaselineConfig):
    """Config C — un seul fragment, une plateforme (baseline basse)."""

    name: str = "mono_source"
    source: str = "reddit"

    def fragment_plan(self, platform_texts):
        fragment_id = PLATFORM_FRAGMENTS.get(self.source, ("F1_reddit", "interest"))[0]
        return {fragment_id: platform_texts.get(self.source, [])}
