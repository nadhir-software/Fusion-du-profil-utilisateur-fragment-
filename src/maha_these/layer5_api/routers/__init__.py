"""Routeurs FastAPI de l'API v1."""

from . import crawl, evaluate, profile, recommend, segments

__all__ = ["crawl", "profile", "recommend", "segments", "evaluate"]
