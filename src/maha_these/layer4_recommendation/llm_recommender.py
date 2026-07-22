"""LLMRecommender — génération d'explications de recommandation par LLM.

Prend une recommandation content-based et produit une justification en
langage naturel ("pourquoi cet item pour ce profil"). Inférence LLM importée
paresseusement. (Phase 3 — LLM Matching.)
"""

from __future__ import annotations

from typing import Any


class LLMRecommender:
    """Génère des explications de recommandation via un LLM."""

    PROMPT = (
        "Explique en une phrase concise pourquoi l'item suivant est pertinent "
        "pour ce profil utilisateur.\nProfil: {profile}\nItem: {item}"
    )

    def __init__(self, model=None, tokenizer=None) -> None:
        self.model = model
        self.tokenizer = tokenizer

    def explain(self, profile: dict[str, Any], item: dict[str, Any]) -> str:
        """Renvoie une explication en langage naturel pour un item."""
        if self.model is None or self.tokenizer is None:
            # TODO(Phase 3): brancher un modèle d'inférence réel.
            raise NotImplementedError(
                "LLMRecommender nécessite un modèle + tokenizer (Phase 3)."
            )
        prompt = self.PROMPT.format(profile=profile, item=item)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=80, temperature=0.3)
        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return text.split(prompt)[-1].strip()

    def explain_batch(
        self, profile: dict[str, Any], recommendations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Enrichit chaque recommandation d'une clé ``explanation``."""
        return [
            {**rec, "explanation": self.explain(profile, rec)}
            for rec in recommendations
        ]
