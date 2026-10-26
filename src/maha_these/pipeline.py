"""FederatedProfilingPipeline — orchestration bout-en-bout.

Chaîne complète, alignée sur le diagramme d'architecture :

    crawl (RAM) → preprocess → fragment → train local (Δθ)
                → agrégation fédérée (θ_global) → génération de profil → store

Toutes les données transitent dans un ``SessionBuffer`` (RAM) effacé en fin de
run (garantie « ne pas enregistrer les data »). Seuls les Δθ puis le profil
final anonymisé quittent la session.

Les dépendances ML lourdes (transformers, peft, trl, torch) sont importées
paresseusement : ce module s'importe sans la pile ``[ai]`` installée. Les
étapes ML sont isolées dans des méthodes surchargées par les tests.
"""

from __future__ import annotations

import os
from typing import Any

from maha_these.core.anonymizer import DataAnonymizer
from maha_these.core.base_agent import BaseAgent
from maha_these.core.orchestrator import OrchestrationAgent
from maha_these.layer2_federated.fragment_builder import FragmentBuilder
from maha_these.layer2_federated.lora_config import DEFAULT_LORA_CFG
from maha_these.layer2_federated.preprocessor import PreprocessorAgent
from maha_these.layer2_federated.system_prompts import SYSTEM_PROMPTS
from maha_these.layer2_federated.trainer_agent import TrainerAgent
from maha_these.layer3_profile.aggregator import FederatedAggregator
from maha_these.layer3_profile.profile_generator import ProfileGenerator
from maha_these.layer3_profile.profile_store import ProfileStore

# plateforme -> (fragment_id, signal_type)
PLATFORM_FRAGMENTS: dict[str, tuple[str, str]] = {
    "reddit": ("F1_reddit", "interest"),
    "linkedin": ("F2_linkedin", "professional"),
    "amazon": ("F3_amazon", "purchase"),
}


def unified_user_hash(targets: dict[str, str]) -> str:
    """Hash unifié du profil, dérivé de tous les identifiants fournis.

    Un utilisateur possède des identifiants distincts par plateforme ; le profil
    global est indexé par le hash de leur combinaison ordonnée. Fonction pure,
    réutilisée par l'API pour renvoyer le hash à interroger ensuite.
    """
    joined = "|".join(f"{p}:{i}" for p, i in sorted(targets.items()) if i)
    return DataAnonymizer().hash_id(joined)


class FederatedProfilingPipeline:
    """Pipeline fédéré complet (couches 1 → 3)."""

    def __init__(
        self, crawlers: dict[str, BaseAgent], config: dict[str, Any] | None = None
    ) -> None:
        self.orchestrator = OrchestrationAgent(crawlers)
        self.config = config or {}
        self.lora_cfg = self.config.get("lora", dict(DEFAULT_LORA_CFG))
        self.training_cfg = self.config.get("training", {})
        self.fed_cfg = self.config.get("federated", {})

    # ------------------------------------------------------------------ #
    # Entrée principale
    # ------------------------------------------------------------------ #
    def run(self, targets: dict[str, str]) -> dict[str, Any]:
        """Exécute le pipeline complet pour un utilisateur.

        Args:
            targets: ``{platform: identifier}`` (identifier vide -> ignoré).

        Returns:
            Résumé non sensible : statut, ``user_hash`` unifié, plateformes.
        """
        buf = self.orchestrator.collect(targets)
        try:
            outputs = []
            for platform, data in buf.items():
                texts = PreprocessorAgent().run(data)["texts"]
                if not texts:
                    continue
                dataset, meta = self._build_fragment(
                    platform, texts, data.get("user_hash", "anonymous")
                )
                outputs.append(self._train_fragment(meta.fragment_id, dataset))

            platforms = buf.platforms()
            if not outputs:
                return {"status": "no_data", "platforms": platforms}

            theta_global = self._aggregate(outputs)
            user_hash = unified_user_hash(targets)
            profile = self._generate_profile(theta_global, user_hash, platforms)
            profile.setdefault("user_hash", user_hash)
            profile["platforms_covered"] = platforms
            ProfileStore.save(profile)

            return {
                "status": "success",
                "user_hash": user_hash,
                "platforms": platforms,
                "n_fragments": len(outputs),
            }
        finally:
            buf.clear()  # effacement RAM garanti, même en cas d'exception

    # ------------------------------------------------------------------ #
    # Étapes (surchargeables pour les tests — isolent la pile ML)
    # ------------------------------------------------------------------ #
    def _build_fragment(self, platform: str, texts: list[str], user_hash: str):
        fragment_id, signal_type = PLATFORM_FRAGMENTS.get(
            platform, (f"F_{platform}", "interest")
        )
        return FragmentBuilder(fragment_id, signal_type).build(texts, user_hash)

    def _train_fragment(self, fragment_id: str, dataset):
        trainer = TrainerAgent(
            fragment_id=fragment_id,
            system_prompt=SYSTEM_PROMPTS.get(fragment_id, ""),
            lora_cfg=self.lora_cfg,
            base_model_name=self.training_cfg.get(
                "base_model", "mistralai/Mistral-7B-Instruct-v0.3"
            ),
            training_cfg=self.training_cfg,
        )
        # Round 0 : chaque fragment part du modèle de base (global_weights=None).
        return trainer.run(dataset, global_weights=None)

    def _aggregate(self, outputs) -> dict:
        aggregator = FederatedAggregator(
            method=self.fed_cfg.get("algorithm", "fedavg"),
            mu=self.fed_cfg.get("mu", 0.01),
        )
        return aggregator.aggregate(outputs)

    def _generate_profile(
        self, theta_global: dict, user_hash: str, platforms: list[str]
    ) -> dict:
        model, tokenizer = self._load_global_model(theta_global)
        return ProfileGenerator().generate(model, tokenizer, user_hash)

    def _load_global_model(self, theta_global: dict):
        return load_global_model(theta_global, self.lora_cfg, self.training_cfg)


def load_global_model(theta_global: dict, lora_cfg: dict, training_cfg: dict):
    """Charge le modèle de base + applique θ_global (imports ML paresseux).

    Réutilisé par le pipeline et par les baselines d'évaluation.
    """
    import torch
    from peft import get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    from maha_these.layer2_federated.lora_config import LoRAConfigurator

    base = training_cfg.get("base_model", "mistralai/Mistral-7B-Instruct-v0.3")
    quant = None
    if training_cfg.get("load_in_4bit", True):
        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
    model = AutoModelForCausalLM.from_pretrained(
        base,
        quantization_config=quant,
        device_map="auto",
    )
    model = get_peft_model(model, LoRAConfigurator(lora_cfg).build())
    if theta_global:
        model.load_state_dict(theta_global, strict=False)
    tokenizer = AutoTokenizer.from_pretrained(base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def build_default_pipeline(
    config: dict[str, Any] | None = None,
) -> FederatedProfilingPipeline:
    """Construit un pipeline avec les 3 crawlers, identifiants Reddit via env."""
    from maha_these.layer1_crawling import (
        AmazonCrawlerAgent,
        LinkedInCrawlerAgent,
        RedditCrawlerAgent,
    )

    reddit_cfg = {
        "client_id": os.getenv("REDDIT_CLIENT_ID", ""),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", ""),
        "user_agent": os.getenv("REDDIT_USER_AGENT", "FederatedProfiler/1.0"),
    }
    crawlers: dict[str, BaseAgent] = {
        "reddit": RedditCrawlerAgent(reddit_cfg),
        "linkedin": LinkedInCrawlerAgent(),
        "amazon": AmazonCrawlerAgent(),
    }
    return FederatedProfilingPipeline(crawlers, config)
