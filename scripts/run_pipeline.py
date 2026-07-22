"""CLI — lance le pipeline fédéré réel (crawl → train → profil).

Prérequis : extras ``[ai]`` + ``[crawl]`` installés, ``.env`` renseigné
(identifiants Reddit + token HuggingFace), et accès au modèle Mistral-7B.
Voir RUNBOOK.md pour la procédure complète.

⚠️ Comme les profils vivent en RAM par process, ce script affiche le profil
généré mais NE peuple PAS le registre de l'API en cours d'exécution. Pour
peupler le dashboard, utiliser plutôt ``POST /api/v1/crawl`` (cf. RUNBOOK).

Exemple :
    python scripts/run_pipeline.py --reddit spez \
        --linkedin https://www.linkedin.com/in/xxx/ \
        --amazon  https://www.amazon.com/gp/profile/xxx/
"""

from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline fédéré de profilage.")
    parser.add_argument("--reddit", required=True, help="username Reddit")
    parser.add_argument("--linkedin", default="", help="URL profil LinkedIn public")
    parser.add_argument("--amazon", default="", help="URL profil Amazon public")
    parser.add_argument(
        "--config", default="config/config.yaml", help="chemin config YAML"
    )
    args = parser.parse_args()

    # Charge le .env (identifiants) si python-dotenv est disponible.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    # Charge la config YAML si présente.
    config = None
    try:
        import yaml

        with open(args.config, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[info] config introuvable ({args.config}), valeurs par défaut.")

    from maha_these.pipeline import build_default_pipeline

    pipeline = build_default_pipeline(config)
    targets = {
        "reddit": args.reddit,
        "linkedin": args.linkedin,
        "amazon": args.amazon,
    }
    result = pipeline.run(targets)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
