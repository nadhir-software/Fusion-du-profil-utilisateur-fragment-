"""RedditCrawlerAgent — collecte via PRAW (+ MCP Server Reddit).

Statut : Phase 0 (réalisée). L'accès réseau réel nécessite les identifiants
Reddit (voir .env : REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / REDDIT_USER_AGENT).
Sans ``praw`` installé ou sans identifiants, l'agent lève une erreur explicite.
"""

from __future__ import annotations

from typing import Any

from .base_crawler import CrawlerAgent


class RedditCrawlerAgent(CrawlerAgent):
    """Crawler Reddit basé sur PRAW."""

    platform = "reddit"
    name = "reddit_crawler"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.limit = self.config.get("limit", 100)
        self._reddit = None  # client PRAW paresseux

    def _client(self):
        if self._reddit is None:
            try:
                import praw  # import paresseux : dépendance optionnelle
            except ImportError as exc:  # pragma: no cover
                raise ImportError(
                    "praw est requis pour RedditCrawlerAgent. "
                    "Installez-le : pip install praw"
                ) from exc
            self._reddit = praw.Reddit(
                client_id=self.config["client_id"],
                client_secret=self.config["client_secret"],
                user_agent=self.config["user_agent"],
            )
        return self._reddit

    def crawl_user(self, identifier: str) -> dict[str, Any]:
        """Collecte posts + commentaires publics d'un utilisateur Reddit."""
        reddit = self._client()
        user = reddit.redditor(identifier)
        posts = [
            {
                "id": p.id,
                "title": p.title,
                "body": p.selftext,
                "subreddit": str(p.subreddit),
                "score": p.score,
                "created_utc": p.created_utc,
                "type": "post",
            }
            for p in user.submissions.new(limit=self.limit)
        ]
        comments = [
            {
                "id": c.id,
                "body": c.body,
                "subreddit": str(c.subreddit),
                "score": c.score,
                "created_utc": c.created_utc,
                "type": "comment",
            }
            for c in user.comments.new(limit=self.limit * 2)
        ]
        return {"username": identifier, "posts": posts, "comments": comments}
