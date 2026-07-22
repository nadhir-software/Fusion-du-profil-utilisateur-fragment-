"""Couche coeur — abstractions partagées par toutes les couches.

Contient :
- BaseAgent      : interface abstraite commune à tous les agents.
- data_models    : modèles Pydantic (Post, Comment, Fragment, Profile...).
- DataAnonymizer : anonymisation SHA-256 + nettoyage PII dès la collecte.
- SessionBuffer  : tampon RAM isolé par session (aucune persistance disque).
"""

from .anonymizer import DataAnonymizer
from .base_agent import BaseAgent
from .data_models import Comment, Fragment, Post, TrainerOutput, UserProfile
from .session_buffer import SessionBuffer

__all__ = [
    "BaseAgent",
    "DataAnonymizer",
    "SessionBuffer",
    "Post",
    "Comment",
    "Fragment",
    "UserProfile",
    "TrainerOutput",
]
