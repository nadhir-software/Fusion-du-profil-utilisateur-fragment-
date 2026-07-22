"""ProfileGenerator — génération du profil global par inférence LLM.

À partir du modèle de base + θ_global (poids LoRA agrégés), génère un profil
JSON structuré pour un ``user_hash``. Ne stocke jamais l'identité réelle.
L'inférence (transformers) est importée paresseusement.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

SYSTEM_PROMPT = """Tu es expert en profilage utilisateur.
À partir des patterns comportementaux appris sur plusieurs plateformes (forums,
réseau professionnel, e-commerce), génère un profil unifié structuré couvrant :
centres d'intérêt, besoins implicites, profil professionnel, habitudes de
consommation, segments marketing. Réponds UNIQUEMENT en JSON valide."""


class ProfileGenerator:
    """Génère un profil unifié via inférence LLM."""

    def __init__(self, system_prompt: str = SYSTEM_PROMPT) -> None:
        self.system_prompt = system_prompt

    def generate(self, model, tokenizer, user_hash: str) -> dict[str, Any]:
        """Génère et parse le profil JSON pour ``user_hash``."""
        prompt = (
            f"[INST] {self.system_prompt}\n"
            f"Génère le profil pour user:{user_hash} [/INST]"
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs, max_new_tokens=512, temperature=0.1, do_sample=True
        )
        raw = tokenizer.decode(outputs[0], skip_special_tokens=True)
        json_str = raw.split("[/INST]")[-1].strip()
        return self._parse(json_str, user_hash)

    def _parse(self, json_str: str, user_hash: str) -> dict[str, Any]:
        try:
            profile = json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return {
                "user_hash": user_hash,
                "error": "json_parse_failed",
                "raw": json_str,
            }
        profile["user_hash"] = user_hash  # jamais l'identité réelle
        profile["profile_version"] = "federated"
        profile["generated_at"] = datetime.now(timezone.utc).isoformat()
        return profile
