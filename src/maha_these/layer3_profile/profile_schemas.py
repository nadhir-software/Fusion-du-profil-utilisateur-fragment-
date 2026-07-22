"""Schéma JSON du profil utilisateur global unifié.

Sert de contrat pour la génération (ProfileGenerator) et la validation
(ProfileStore / API). Aligné sur le modèle Pydantic ``UserProfile``.
"""

from __future__ import annotations

USER_PROFILE_SCHEMA: dict = {
    "type": "object",
    "required": ["user_hash", "interests"],
    "properties": {
        "user_hash": {"type": "string"},
        "interests": {"type": "array", "items": {"type": "string"}},
        "needs": {
            "type": "object",
            "properties": {
                "implicit": {"type": "array", "items": {"type": "string"}},
                "explicit": {"type": "array", "items": {"type": "string"}},
            },
        },
        "professional": {
            "type": "object",
            "properties": {
                "sector": {"type": "string"},
                "skills": {"type": "array", "items": {"type": "string"}},
                "seniority": {"type": "string"},
            },
        },
        "consumption": {
            "type": "object",
            "properties": {
                "preferred_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "price_sensitivity": {"type": "string"},
            },
        },
        "marketing_segments": {"type": "array", "items": {"type": "string"}},
        "platforms_covered": {"type": "array", "items": {"type": "string"}},
        "profile_version": {"type": "string"},
        "generated_at": {"type": "string"},
    },
}

#: Gabarit vide conforme au schéma, utile pour les tests / fallback.
EMPTY_PROFILE: dict = {
    "user_hash": "",
    "interests": [],
    "needs": {"implicit": [], "explicit": []},
    "professional": {"sector": "", "skills": [], "seniority": ""},
    "consumption": {"preferred_categories": [], "price_sensitivity": ""},
    "marketing_segments": [],
    "platforms_covered": [],
    "profile_version": "federated",
}
