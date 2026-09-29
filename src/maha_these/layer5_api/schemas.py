"""Modèles Pydantic — validation des I/O de l'API REST."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CrawlRequest(BaseModel):
    reddit_username: str
    linkedin_url: Optional[str] = None
    amazon_profile_url: Optional[str] = None


class CrawlResponse(BaseModel):
    status: str
    job_id: str
    # hash unifié sous lequel le profil sera stocké (à interroger ensuite via
    # GET /api/v1/profile/{user_hash}).
    user_hash: str


class UserRecoRequest(BaseModel):
    user_hash: str
    catalog: list[dict[str, Any]]
    top_k: int = 10


class CampaignRequest(BaseModel):
    # {"name": ..., "description": ..., "target_category": ...}
    campaign: dict[str, Any]
    threshold: float = 0.5


class CatalogRecoRequest(BaseModel):
    user_hash: str
    top_k: int = 10


class ProfileResponse(BaseModel):
    user_hash: str
    interests: list[str] = Field(default_factory=list)
    needs: dict[str, Any] = Field(default_factory=dict)
    professional: dict[str, Any] = Field(default_factory=dict)
    consumption: dict[str, Any] = Field(default_factory=dict)
    marketing_segments: list[str] = Field(default_factory=list)
    platforms_covered: list[str] = Field(default_factory=list)
    profile_version: str = "federated"
    generated_at: str = ""
