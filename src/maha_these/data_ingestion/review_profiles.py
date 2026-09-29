"""Construction de profils utilisateurs RÉELS à partir d'avis Amazon.

Pipeline conforme au principe **RAM-only** : les avis sont streamés depuis le
dataset (jamais tout en mémoire), groupés par utilisateur, puis **chaque
utilisateur est traité un à un dans un ``SessionBuffer``** (RAM) — profil
construit, buffer effacé. Seul le profil dérivé (anonymisé) subsiste.

Le profil d'un utilisateur est dérivé de ce qu'il a noté/commenté : catégories
et titres des items (via l'index catalogue) + texte de ses avis → centres
d'intérêt, habitudes de consommation.

Note sur le volume : ``max_records`` borne le nombre d'avis lus (échantillon
streamé). Pour un passage à l'échelle complet (571 M d'avis), on trierait les
avis par utilisateur en amont ; ici on borne pour rester léger et reproductible.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from maha_these.core.anonymizer import DataAnonymizer
from maha_these.core.session_buffer import SessionBuffer
from maha_these.layer3_profile.heuristic_profile import HeuristicProfileBuilder

from .amazon_reviews import stream_reviews


def build_profiles_from_reviews(
    reviews_path: str | Path,
    catalog_index: dict[str, dict[str, Any]] | None = None,
    max_records: int = 200_000,
    max_users: int = 100,
    min_reviews: int = 3,
) -> list[dict[str, Any]]:
    """Construit des profils réels à partir des avis (streamé, RAM par user).

    Args:
        reviews_path: fichier JSONL d'avis (``download_reviews``).
        catalog_index: ``{parent_asin: {"name", "category"}}`` pour enrichir.
        max_records: nombre max d'avis lus (borne mémoire).
        max_users: nombre max de profils produits.
        min_reviews: nombre min d'avis pour retenir un utilisateur.

    Returns:
        Liste de profils (mêmes champs que ``HeuristicProfileBuilder.build``).
    """
    catalog_index = catalog_index or {}
    anonymizer = DataAnonymizer()
    builder = HeuristicProfileBuilder()

    # 1) grouper les avis par utilisateur (borné par max_records)
    by_user: dict[str, list[dict]] = defaultdict(list)
    for review in stream_reviews(reviews_path, max_records=max_records):
        if review["user_id"]:
            by_user[review["user_id"]].append(review)

    # 2) un utilisateur à la fois en RAM → profil → effacement
    profiles: list[dict[str, Any]] = []
    for user_id, reviews in by_user.items():
        if len(reviews) < min_reviews:
            continue
        with SessionBuffer() as buf:  # RAM only, vidé à la sortie du bloc
            session_reviews = [
                {
                    "product": catalog_index.get(r["parent_asin"], {}).get("name")
                    or r["title"]
                    or "item",
                    "category": catalog_index.get(r["parent_asin"], {}).get(
                        "category", "Amazon"
                    ),
                    "text": f"{r.get('title', '')} {r.get('text', '')}".strip(),
                }
                for r in reviews
            ]
            data = anonymizer.anonymize(
                {"username": user_id, "reviews": session_reviews}
            )
            buf.write("amazon", data)
            profiles.append(builder.build(buf.read("amazon"), data["user_hash"]))
        if len(profiles) >= max_users:
            break
    return profiles
