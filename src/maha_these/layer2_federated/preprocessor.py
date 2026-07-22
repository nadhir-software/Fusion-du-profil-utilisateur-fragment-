"""PreprocessorAgent — nettoyage, normalisation et filtrage des silos.

Charge un silo local, nettoie/normalise le texte, filtre par longueur, puis
produit une liste d'exemples texte prêts pour la tokenisation/fragmentation.
La tokenisation effective est déléguée au FragmentBuilder (qui connaît le
tokenizer du modèle de base).
"""

from __future__ import annotations

from typing import Any

from maha_these.core.anonymizer import DataAnonymizer
from maha_these.core.base_agent import BaseAgent


class PreprocessorAgent(BaseAgent):
    """Prétraitement local d'un silo avant fragmentation."""

    name = "preprocessor"

    def __init__(self, min_length: int = 5, max_length: int = 512) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.anonymizer = DataAnonymizer()

    def _extract_texts(self, silo_data: dict[str, Any]) -> list[str]:
        texts: list[str] = []
        for key, items in silo_data.items():
            if key == "user_hash" or not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                parts = [item.get("title", ""), item.get("body", ""), item.get("text", "")]
                joined = " ".join(p for p in parts if p).strip()
                if joined:
                    texts.append(joined)
        return texts

    def normalize(self, text: str) -> str:
        """Nettoyage PII résiduel + normalisation des espaces."""
        text = self.anonymizer.clean_text(text)
        return " ".join(text.split())

    def filter_length(self, texts: list[str]) -> list[str]:
        return [
            t
            for t in texts
            if self.min_length <= len(t.split()) <= self.max_length
        ]

    def run(self, silo_data: dict[str, Any]) -> dict[str, Any]:
        """Renvoie ``{"status", "user_hash", "texts": [...]}``."""
        texts = [self.normalize(t) for t in self._extract_texts(silo_data)]
        texts = self.filter_length(texts)
        return {
            "status": "success",
            "user_hash": silo_data.get("user_hash", "anonymous"),
            "texts": texts,
        }
