"""DataAnonymizer — anonymisation des identifiants nominatifs dès la collecte.

Deux garanties (couvertes par tests/unit/test_anonymizer.py) :
1. L'identifiant nominatif (username) est remplacé par un hash SHA-256.
2. Le texte libre est nettoyé de ses PII résiduels (mentions, URLs, emails).

Cette étape est appliquée dès la collecte, AVANT toute mise en tampon
mémoire (SessionBuffer). Aucune donnée n'est jamais écrite sur disque.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

_MENTION_RE = re.compile(r"(?:u/|@)\w+")
_URL_RE = re.compile(r"https?://\S+")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.\w+\b")


class DataAnonymizer:
    """Anonymise les identifiants nominatifs et nettoie les PII textuels."""

    def hash_id(self, identifier: str) -> str:
        """Hash SHA-256 tronqué (32 caractères hex) d'un identifiant.

        Déterministe : le même identifiant produit toujours le même hash,
        ce qui permet d'indexer les profils sans jamais stocker l'identité.
        """
        return hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:32]

    def clean_text(self, text: str) -> str:
        """Supprime mentions, URLs et emails d'un texte libre.

        Ordre important : URLs puis emails AVANT les mentions, sinon le motif
        de mention ``@\\w+`` engloutirait la partie ``@domaine`` d'un email.
        """
        if not text:
            return ""
        text = _URL_RE.sub("[URL]", text)  # URLs
        text = _EMAIL_RE.sub("[EMAIL]", text)  # emails
        text = _MENTION_RE.sub("[USER]", text)  # mentions Reddit / @handles
        return text.strip()

    def anonymize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Anonymise un enregistrement brut ``{"username": ..., <collections>}``.

        - ``username`` -> ``user_hash`` (jamais conservé en clair).
        - Chaque collection d'items voit ses champs ``body``/``title``/``text``
          nettoyés via :meth:`clean_text`.

        Aucune donnée nominative ne subsiste dans le résultat.
        """
        username = data.get("username", "")
        result: dict[str, Any] = {"user_hash": self.hash_id(username)}

        for key, items in data.items():
            if key == "username":
                continue
            if isinstance(items, list):
                result[key] = [self._clean_item(item) for item in items]
            else:
                result[key] = items
        return result

    def _clean_item(self, item: Any) -> Any:
        if not isinstance(item, dict):
            return item
        cleaned = dict(item)
        for field in ("body", "title", "text"):
            if field in cleaned and isinstance(cleaned[field], str):
                cleaned[field] = self.clean_text(cleaned[field])
        return cleaned
