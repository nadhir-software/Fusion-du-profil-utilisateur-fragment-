"""Chargement d'un catalogue d'items depuis Amazon Reviews 2023 (McAuley/UCSD).

Dataset **public, publié pour la recherche** (≠ scraping) :
https://amazon-reviews-2023.github.io/

À CITER dans la thèse :
    Yupeng Hou, Jiacheng Li, Zhankui He, An Yan, Xiusi Chen, Julian McAuley,
    "Bridging Language and Items for Retrieval and Recommendation", 2024.

Ce module télécharge la métadonnée produits d'une catégorie (petite par défaut)
et la convertit au format catalogue attendu par le moteur de recommandation :
``{"id", "name", "description", "category"}``. Les fichiers téléchargés sont
mis en cache local (``data/catalogs/``, gitignoré) — ce sont des données
produits publiques, pas des données utilisateurs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ID = "McAuley-Lab/Amazon-Reviews-2023"
DEFAULT_DIR = Path("data/catalogs")

# Petites catégories (Mo) → téléchargement rapide.
SMALL_CATEGORIES = {
    "Subscription_Boxes": 1.4,
    "Gift_Cards": 2.0,
    "Magazine_Subscriptions": 4.1,  # défaut : thématiquement diversifié
}


def download_category(
    category: str = "Magazine_Subscriptions", dest_dir: str | Path = DEFAULT_DIR
) -> Path:
    """Télécharge le fichier de métadonnées d'une catégorie et renvoie son chemin.

    Utilise le cache HuggingFace : un re-téléchargement est évité si le fichier
    est déjà présent.
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "huggingface_hub est requis pour télécharger le dataset Amazon. "
            "Il est fourni avec transformers/sentence-transformers ([ai])."
        ) from exc

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    path = hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename=f"raw/meta_categories/meta_{category}.jsonl",
        local_dir=str(dest),
    )
    return Path(path)


def _item_from_meta(obj: dict[str, Any], index: int) -> dict[str, Any] | None:
    """Convertit un enregistrement de métadonnée McAuley en item de catalogue."""
    title = (obj.get("title") or "").strip()
    if not title:
        return None
    parts = list(obj.get("features") or []) + list(obj.get("description") or [])
    description = " ".join(str(p) for p in parts).strip()[:300]
    category = (
        obj.get("main_category") or (obj.get("categories") or [""])[-1] or "Amazon"
    )
    return {
        "id": obj.get("parent_asin") or f"item_{index}",
        "name": title,
        "description": description,
        "category": str(category),
    }


def load_catalog(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    """Charge un catalogue depuis un fichier JSONL de métadonnées McAuley.

    Args:
        path: chemin du fichier ``meta_<Category>.jsonl``.
        limit: nombre maximum d'items à charger (None = tous).

    Returns:
        Liste d'items ``{"id", "name", "description", "category"}``.
    """
    items: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for index, line in enumerate(f):
            if limit is not None and len(items) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = _item_from_meta(obj, index)
            if item is not None:
                items.append(item)
    return items


def download_reviews(
    category: str = "Magazine_Subscriptions", dest_dir: str | Path = DEFAULT_DIR
) -> Path:
    """Télécharge le fichier d'AVIS (interactions user-item) d'une catégorie."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "huggingface_hub est requis pour télécharger les avis Amazon "
            "(fourni avec transformers/sentence-transformers)."
        ) from exc

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    path = hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename=f"raw/review_categories/{category}.jsonl",
        local_dir=str(dest),
    )
    return Path(path)


def stream_reviews(path: str | Path, max_records: int | None = None):
    """Streame les avis (interactions user-item) depuis un JSONL McAuley.

    Générateur : ne charge jamais tout le fichier en mémoire. Chaque avis est
    yieldé sous la forme ``{user_id, parent_asin, rating, title, text}``.
    """
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_records is not None and i >= max_records:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield {
                "user_id": obj.get("user_id", ""),
                "parent_asin": obj.get("parent_asin") or obj.get("asin", ""),
                "rating": obj.get("rating"),
                "title": obj.get("title", ""),
                "text": obj.get("text", ""),
            }
