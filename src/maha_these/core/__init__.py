"""Couche coeur — abstractions partagées par toutes les couches.

Contient :
- BaseAgent      : interface abstraite commune à tous les agents.
- data_models    : modèles Pydantic (Post, Comment, Fragment, UserProfile...).
- DataAnonymizer : anonymisation SHA-256 + nettoyage PII dès la collecte.
- LocalDataSilo  : stockage local isolé par plateforme.
"""

from .anonymizer import DataAnonymizer
from .base_agent import BaseAgent
from .data_models import Comment, Fragment, Post, TrainerOutput, UserProfile
from .local_silo import LocalDataSilo

__all__ = [
    "BaseAgent",
    "DataAnonymizer",
    "LocalDataSilo",
    "Post",
    "Comment",
    "Fragment",
    "UserProfile",
    "TrainerOutput",
]
