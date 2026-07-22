"""ProfileEncoder — encodage Sentence-BERT des profils et items.

Fournit une représentation vectorielle unique (embeddings) partagée par le
recommandeur content-based et le clustering de segments. Le modèle
Sentence-Transformers est chargé paresseusement.
"""

from __future__ import annotations

from typing import Any


class ProfileEncoder:
    """Encodeur d'embeddings basé sur Sentence-BERT."""

    def __init__(self, model_name: str = "all-mpnet-base-v2") -> None:
        self.model_name = model_name
        self._encoder = None

    @property
    def encoder(self):
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover
                raise ImportError(
                    "sentence-transformers est requis pour ProfileEncoder. "
                    "Installez : pip install sentence-transformers"
                ) from exc
            self._encoder = SentenceTransformer(self.model_name)
        return self._encoder

    @staticmethod
    def profile_to_text(profile: dict[str, Any]) -> str:
        """Aplatit un profil en un texte encodable."""
        parts = [
            " ".join(profile.get("interests", [])),
            " ".join(profile.get("needs", {}).get("implicit", [])),
            profile.get("professional", {}).get("sector", ""),
            " ".join(profile.get("consumption", {}).get("preferred_categories", [])),
        ]
        return " ".join(p for p in parts if p)

    def encode(self, texts: list[str]):
        """Encode une liste de textes en matrice d'embeddings."""
        return self.encoder.encode(texts)

    def encode_profiles(self, profiles: list[dict[str, Any]]):
        """Encode une liste de profils."""
        return self.encode([self.profile_to_text(p) for p in profiles])
