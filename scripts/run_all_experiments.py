"""Runner unique — enchaîne les campagnes EXP-01..05 en une commande.

Point d'entrée pensé pour être lancé **tel quel sur la machine GPU** une fois
la pile ``[ai]`` installée (torch/transformers/peft/trl + accès Mistral-7B, cf.
RUNBOOK.md). Il prépare des données synthétiques reproductibles (seed fixe),
exécute les cinq campagnes, journalise dans MLflow et écrit un **résumé de
métriques** (JSON dérivé — pas de données brutes) dans ``reports/experiments/``.

Deux modes :

* ``--mode real``  : entraînement LoRA réel (nécessite GPU + pile ``[ai]``).
  Si la pile est absente, le script s'arrête proprement avec la marche à suivre.
* ``--mode smoke`` (défaut) : remplace les étapes ML lourdes par un profil
  heuristique. **Vérifie uniquement le câblage** (données → fragments →
  métriques → MLflow → JSON) — les chiffres ne sont PAS scientifiques. Utile
  ici (sans GPU) et en CI pour prouver que la chaîne tient de bout en bout.

Exemples :
    python scripts/run_all_experiments.py                 # smoke (wiring)
    python scripts/run_all_experiments.py --mode real     # campagne GPU
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Rendre les packages `evaluation` et `maha_these` importables.
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "src"))

OUT_DIR = _REPO / "reports" / "experiments"

# Petit catalogue étiqueté par persona (vérité terrain pour EXP-03).
PERSONA_CATALOG: dict[str, list[tuple[str, str]]] = {
    "tech_ml": [
        ("gpu rtx 4070", "pytorch model training neural gpu deep learning"),
        ("machine learning book", "algorithm dataset python code learning"),
        ("mechanical keyboard", "programming code developer python"),
    ],
    "fitness_cycling": [
        ("carbon road bike", "cycling ride endurance cadence watts climb"),
        ("running shoes", "marathon training recovery gear"),
        ("heart rate monitor", "training nutrition endurance sport"),
    ],
    "foodie_cooking": [
        ("robot cuiseur", "recipe kitchen dish meal sauce ingredients"),
        ("chef knife set", "kitchen roast spices baking"),
        ("cast iron pan", "flavor meal roast dish"),
    ],
    "finance_invest": [
        ("finance book", "portfolio dividend market index etf returns"),
        ("premium notebook", "budget savings strategy planning"),
        ("second monitor", "market analysis trading risk"),
    ],
    "gamer_tech": [
        ("gaming headset", "fps gameplay console controller latency"),
        ("graphics card", "fps graphics rig build monitor"),
        ("gaming chair", "gaming build rig console"),
    ],
    "eco_outdoor": [
        ("reusable bottle", "sustainable reusable recycle zero waste"),
        ("hiking backpack", "trail hiking nature outdoor"),
        ("compost bin", "compost sustainable plants solar recycle"),
    ],
}


# --------------------------------------------------------------------------- #
# Trackers
# --------------------------------------------------------------------------- #
class _NullTracker:
    """Tracker inerte (mode smoke / MLflow désactivé)."""

    def run(self, name):
        import contextlib

        return contextlib.nullcontext()

    def log_params(self, params):
        pass

    def log_metrics(self, metrics):
        pass


def _make_tracker(mode: str, use_mlflow: bool):
    if mode == "real" and use_mlflow:
        from evaluation.mlflow_tracker import MLflowTracker

        return MLflowTracker(experiment_name="federated_profiling_campaign")
    return _NullTracker()


# --------------------------------------------------------------------------- #
# Préparation des données (synthétique, reproductible)
# --------------------------------------------------------------------------- #
def prepare_data(seed: int, user: str):
    """Construit ``platform_texts`` + ``holdout`` + persona pour un utilisateur."""
    from maha_these.data_generation.synthetic import SyntheticDataGenerator

    gen = SyntheticDataGenerator(seed)
    reddit = gen.generate_reddit(user)
    amazon = gen.generate_amazon(user)
    linkedin = gen.generate_linkedin(user)

    platform_texts = {
        "reddit": [f"{p['title']} {p['body']}" for p in reddit["posts"]]
        + [c["body"] for c in reddit["comments"]],
        "amazon": [r["text"] for r in amazon["reviews"]],
        "linkedin": [f"{p['headline']} {p['text']}" for p in linkedin["profile"]],
    }
    persona = gen.persona(user)
    # vérité terrain (proxy) : mots-clés + subreddits du persona, minuscules
    holdout = [w.lower() for w in persona["keywords"] + persona["subreddits"]]
    return platform_texts, holdout, persona


def build_catalog(persona_name: str):
    """Catalogue plat + identifiants des items pertinents pour ce persona."""
    catalog, relevant = [], []
    for persona, items in PERSONA_CATALOG.items():
        for name, desc in items:
            item_id = f"{persona}:{name}"
            catalog.append(
                {"id": item_id, "name": name, "description": desc, "persona": persona}
            )
            if persona == persona_name:
                relevant.append(item_id)
    return catalog, relevant


# --------------------------------------------------------------------------- #
# Mode smoke : remplace les étapes ML par des heuristiques (wiring only)
# --------------------------------------------------------------------------- #
def _smoke_profile(platform_texts: dict[str, list[str]], user_hash: str) -> dict:
    """Profil heuristique : interests = tokens fréquents (hors stopwords)."""
    from maha_these.layer3_profile.heuristic_profile import _STOPWORDS, _WORD_RE

    blob = " ".join(t for texts in platform_texts.values() for t in texts).lower()
    words = [w for w in _WORD_RE.findall(blob) if w not in _STOPWORDS]
    interests = [w for w, _ in Counter(words).most_common(20)]
    return {"user_hash": user_hash, "interests": interests}


def install_smoke_patches(monkeypatch_target) -> None:
    """Injecte le profil heuristique à la place de l'entraînement LoRA réel."""
    import evaluation.baselines as baselines

    def smoke_run(self, platform_texts, user_hash="exp_user"):
        plan = self.fragment_plan(platform_texts)
        merged = {"_merged": [t for texts in plan.values() for t in texts]}
        return _smoke_profile(merged, user_hash)

    baselines.BaselineConfig.run_pipeline = smoke_run


def _smoke_recommender(catalog: list[dict]):
    """Reco factice : classe le catalogue par recouvrement de mots-clés."""

    def recommend(profile, k):
        interests = set(profile.get("interests", []))
        ranked = sorted(
            catalog,
            key=lambda c: len(interests & set(c["description"].split())),
            reverse=True,
        )
        return [{"item_id": c["id"]} for c in ranked[:k]]

    return recommend


# --------------------------------------------------------------------------- #
# Exécution des campagnes
# --------------------------------------------------------------------------- #
def run_campaigns(platform_texts, holdout, persona, mode, tracker, only=None):
    from evaluation.baselines import CentralizedConfig, FederatedConfig
    from evaluation.experiments.exp_01_comparison import Exp01Comparison
    from evaluation.experiments.exp_02_fragments import Exp02Fragments
    from evaluation.experiments.exp_03_recommendation import Exp03Recommendation
    from evaluation.experiments.exp_04_lora_rank import Exp04LoraRank
    from evaluation.experiments.exp_05_dp import Exp05DifferentialPrivacy

    def selected(exp_id: str) -> bool:
        return only is None or exp_id in only

    results: dict = {}

    if selected("exp_01"):
        print("-> EXP-01 : fédéré vs centralisé vs mono-source")
        results["exp_01"] = Exp01Comparison(
            platform_texts, holdout, tracker=tracker
        ).run()

    if selected("exp_02"):
        print("-> EXP-02 : impact du nombre de fragments {1, 2, 3}")
        results["exp_02"] = Exp02Fragments(
            platform_texts, holdout, tracker=tracker
        ).run()

    if selected("exp_04"):
        print("-> EXP-04 : ablation du rang LoRA {4, 8, 16, 32}")
        results["exp_04"] = Exp04LoraRank(
            platform_texts, holdout, tracker=tracker
        ).run()

    if selected("exp_05"):
        print("-> EXP-05 : compromis privacy/utility (Differential Privacy)")
        results["exp_05"] = Exp05DifferentialPrivacy(
            platform_texts, holdout, tracker=tracker
        ).run()

    if selected("exp_03"):
        print("-> EXP-03 : qualité de recommandation (fédéré vs centralisé)")
        catalog, relevant = build_catalog(persona["name"])
        profiles_by_config = {
            "federated": FederatedConfig().run_pipeline(platform_texts),
            "centralized": CentralizedConfig().run_pipeline(platform_texts),
        }
        exp03 = Exp03Recommendation(
            profiles_by_config, catalog, relevant, tracker=tracker
        )
        if mode == "smoke":
            exp03._recommend = _smoke_recommender(catalog)
        results["exp_03"] = exp03.run()

    return results


# --------------------------------------------------------------------------- #
# Vérification de la pile ML
# --------------------------------------------------------------------------- #
def ai_stack_available() -> bool:
    return all(
        importlib.util.find_spec(m) is not None
        for m in ("torch", "transformers", "peft")
    )


def _print_summary(results: dict) -> None:
    print("\n================ RÉSUMÉ DES MÉTRIQUES ================")
    print(json.dumps(results, ensure_ascii=False, indent=2, default=str))


def save_results(results: dict, mode: str, seed: int) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUT_DIR / f"results_{mode}_{ts}.json"
    payload = {
        "mode": mode,
        "seed": seed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "SMOKE = câblage seulement, chiffres non scientifiques"
            if mode == "smoke"
            else "campagne réelle (entraînement LoRA)"
        ),
        "results": results,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Runner des campagnes EXP-01..05.")
    parser.add_argument(
        "--mode",
        choices=("smoke", "real"),
        default="smoke",
        help="smoke = câblage (défaut) ; real = entraînement LoRA (GPU requis)",
    )
    parser.add_argument("--seed", type=int, default=42, help="graine reproductible")
    parser.add_argument("--user", default="user_0", help="utilisateur synthétique")
    parser.add_argument(
        "--no-mlflow", action="store_true", help="désactive MLflow (mode real)"
    )
    parser.add_argument(
        "--base-model",
        default=None,
        help="modèle de base (défaut : Mistral-7B). Ex. Qwen/Qwen2.5-0.5B-Instruct",
    )
    parser.add_argument(
        "--epochs", type=int, default=1, help="epochs d'entraînement (mode real)"
    )
    parser.add_argument(
        "--max-seq", type=int, default=256, help="longueur max de séquence (mode real)"
    )
    parser.add_argument(
        "--only",
        default=None,
        help="campagnes à exécuter (CSV), ex. 'exp_01' ou 'exp_01,exp_03'. "
        "Défaut : toutes.",
    )
    args = parser.parse_args()
    only = {c.strip() for c in args.only.split(",") if c.strip()} if args.only else None

    if args.mode == "real":
        # Réglages adaptés à un petit GPU (8 Go) : batch 1, seq courte, 4-bit.
        # Contourne le backend Xet de HuggingFace (téléchargements instables).
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
        import evaluation.baselines as baselines

        baselines.RUNTIME_TRAINING_CFG = {
            "num_train_epochs": args.epochs,
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "max_seq_length": args.max_seq,
            "fp16": True,
            "gradient_checkpointing": True,
            "load_in_4bit": True,
        }
        if args.base_model:
            baselines.RUNTIME_TRAINING_CFG["base_model"] = args.base_model
        print(f"           [real] training_cfg = {baselines.RUNTIME_TRAINING_CFG}")

    if args.mode == "real" and not ai_stack_available():
        print(
            "[stop] Mode 'real' demandé mais la pile [ai] est absente "
            "(torch/transformers/peft).\n"
            "       Installe-la et relance sur GPU :\n"
            "         pip install -e '.[ai]'\n"
            "       Puis suis RUNBOOK.md (accès Mistral-7B via HUGGINGFACE_TOKEN).\n"
            "       Pour vérifier le câblage sans GPU : --mode smoke",
            file=sys.stderr,
        )
        return 1

    print(f"[run_all_experiments] mode={args.mode} seed={args.seed} user={args.user}")
    platform_texts, holdout, persona = prepare_data(args.seed, args.user)
    print(f"           persona = {persona['name']} · holdout = {len(holdout)} tokens")

    if args.mode == "smoke":
        install_smoke_patches(None)

    tracker = _make_tracker(args.mode, use_mlflow=not args.no_mlflow)
    results = run_campaigns(
        platform_texts, holdout, persona, args.mode, tracker, only=only
    )

    _print_summary(results)
    path = save_results(results, args.mode, args.seed)
    print(f"\n[ok] résumé écrit dans {path.relative_to(_REPO)}")
    if args.mode == "smoke":
        print(
            "[note] Mode SMOKE : chiffres non scientifiques (câblage seulement).\n"
            "       Pour les vrais résultats : --mode real sur GPU (RUNBOOK.md)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
