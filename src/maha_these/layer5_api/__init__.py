"""Couche 5 — API REST (FastAPI) & schémas Pydantic."""

from .schemas import (
    CampaignRequest,
    CrawlRequest,
    ProfileResponse,
    UserRecoRequest,
)

__all__ = [
    "CrawlRequest",
    "UserRecoRequest",
    "CampaignRequest",
    "ProfileResponse",
]
