"""PreprocessorAgent — Intelligent Preprocessing Pipeline.

Consomme les données anonymisées d'une plateforme **directement depuis le
tampon mémoire** (SessionBuffer) : nettoyage, normalisation, filtrage par
longueur, puis production d'exemples texte prêts pour la tokenisation /
fragmentation. La tokenisation et la génération d'embeddings sont déléguées en
aval (FragmentBuilder / ProfileEncoder, qui connaissent le tokenizer / modèle).

Aucune lecture disque : l'entrée est un dictionnaire déjà présent en RAM.
"""

from __future__ import annotations

from typing import Any

from maha_these.core.anonymizer import DataAnonymizer
from maha_these.core.base_agent import BaseAgent


class PreprocessorAgent(BaseAgent):
    """Prétraitement local d'une tranche de session (une plateforme)."""

    name = "preprocessor"

    def __init__(self, min_length: int = 5, max_length: int = 512) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.anonymizer = DataAnonymizer()

    def _extract_texts(self, session_data: dict[str, Any]) -> list[str]:
        texts: list[str] = []
        for key, items in session_data.items():
            if key == "user_hash" or not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                parts = [
                    item.get("title", ""),
                    item.get("body", ""),
                    item.get("text", ""),
                ]
                joined = " ".join(p for p in parts if p).strip()
                if joined:
                    texts.append(joined)
        return texts

    def detect_language(self, text: str) -> str | None:
        """Détection de langue (best-effort, dépendance optionnelle).

        Renvoie un code ISO 639-1 (ex. "fr", "en") ou None si ``langdetect``
        n'est pas installé. Sert à filtrer/router par langue en amont.
        """
        try:
            from langdetect import detect  # import paresseux (optionnel)
        except ImportError:
            return None
        try:
            return detect(text)
        except Exception:  # pragma: no cover - texte trop court/ambigu
            return None

    def normalize(self, text: str) -> str:
        """Nettoyage PII résiduel + normalisation des espaces."""
        text = self.anonymizer.clean_text(text)
        return " ".join(text.split())

    def filter_length(self, texts: list[str]) -> list[str]:
        return [
            t for t in texts if self.min_length <= len(t.split()) <= self.max_length
        ]

    def run(self, session_data: dict[str, Any]) -> dict[str, Any]:
        """Prétraite une tranche de session RAM.

        Args:
            session_data: dictionnaire anonymisé d'une plateforme, tel que
                renvoyé par ``SessionBuffer.read(platform)``.

        Returns:
            ``{"status", "user_hash", "texts": [...]}``.
        """
        texts = [self.normalize(t) for t in self._extract_texts(session_data)]
        texts = self.filter_length(texts)
        return {
            "status": "success",
            "user_hash": session_data.get("user_hash", "anonymous"),
            "texts": texts,
        }
