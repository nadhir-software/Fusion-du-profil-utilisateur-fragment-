"""Couche 1 — Crawling multi-plateformes sécurisé.

Collecte de données publiques (Reddit, LinkedIn, Amazon), anonymisation
immédiate (DataAnonymizer) puis stockage local isolé (LocalDataSilo).
"""

from .amazon_crawler import AmazonCrawlerAgent
from .base_crawler import CrawlerAgent
from .linkedin_crawler import LinkedInCrawlerAgent
from .rate_limiter import RateLimiter
from .reddit_crawler import RedditCrawlerAgent

__all__ = [
    "CrawlerAgent",
    "RedditCrawlerAgent",
    "LinkedInCrawlerAgent",
    "AmazonCrawlerAgent",
    "RateLimiter",
]
