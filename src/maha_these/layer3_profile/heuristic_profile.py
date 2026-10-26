"""HeuristicProfileBuilder — profil à partir de signaux multi-plateformes (sans LLM).

Alternative légère au ``ProfileGenerator`` (LLM) : dérive le profil directement
des signaux disponibles, sans Mistral ni GPU :

- **Reddit**   : subreddits fréquentés + mots-clés des posts/commentaires.
- **Amazon**   : catégories d'avis → habitudes de consommation.
- **LinkedIn** : headline + compétences → profil professionnel.

Le profil produit (``profile_version="heuristic"``) alimente le moteur de
recommandation (Sentence-BERT). Entrée : une tranche de session RAM anonymisée.
Aucune écriture disque.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

_WORD_RE = re.compile(r"[a-zA-ZÀ-ÿ]{3,}")

# Stopwords FR + EN (liste volontairement compacte).
_STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "this",
    "with",
    "you",
    "your",
    "are",
    "was",
    "but",
    "not",
    "have",
    "has",
    "had",
    "they",
    "them",
    "then",
    "there",
    "here",
    "what",
    "when",
    "who",
    "why",
    "how",
    "all",
    "any",
    "can",
    "will",
    "just",
    "like",
    "get",
    "got",
    "one",
    "out",
    "about",
    "would",
    "could",
    "should",
    "from",
    "some",
    "more",
    "very",
    "also",
    "into",
    "than",
    "too",
    "its",
    "our",
    "their",
    "his",
    "her",
    "she",
    "him",
    "were",
    "been",
    "being",
    "does",
    "did",
    "les",
    "des",
    "une",
    "que",
    "qui",
    "pas",
    "pour",
    "dans",
    "sur",
    "avec",
    "est",
    "sont",
    "mais",
    "plus",
    "vous",
    "nous",
    "ils",
    "elle",
    "cette",
    "ces",
    "aux",
    "par",
    "son",
    "ses",
    "leur",
    "tout",
    "tous",
    "fait",
    "comme",
    "bien",
    "être",
    "avoir",
    "cela",
    "donc",
    "aussi",
    "vraiment",
    "trop",
    "moi",
    "toi",
    "lui",
    "eux",
    "http",
    "https",
    "com",
    "www",
    "reddit",
    "recommend",
    "best",
    "great",
    "love",
    "new",
    "using",
    # bruit générique des catalogues/avis
    "magazine",
    "magazines",
    "issue",
    "issues",
    "print",
    "subscription",
    "subscriptions",
    "product",
    "item",
    "amazon",
    "read",
    "reading",
    "buy",
    "bought",
}


class HeuristicProfileBuilder:
    """Construit un profil à partir des signaux Reddit / Amazon / LinkedIn."""

    def __init__(self, top_subreddits: int = 8, top_keywords: int = 12) -> None:
        self.top_subreddits = top_subreddits
        self.top_keywords = top_keywords

    def build(self, session_data: dict[str, Any], user_hash: str) -> dict[str, Any]:
        posts = list(session_data.get("posts", []))
        comments = list(session_data.get("comments", []))
        reviews = list(session_data.get("reviews", []))
        linkedin = list(session_data.get("profile", []))
        skills = list(session_data.get("skills", []))
        reddit_items = posts + comments

        # 1) Reddit : subreddits fréquents
        sub_counts = Counter(
            i.get("subreddit", "") for i in reddit_items if i.get("subreddit")
        )
        top_subs = [s for s, _ in sub_counts.most_common(self.top_subreddits) if s]

        # 2) Mots-clés récurrents (toutes sources textuelles)
        texts = [f"{i.get('title', '')} {i.get('body', '')}" for i in reddit_items]
        texts += [r.get("text", "") for r in reviews]
        texts += [f"{p.get('headline', '')} {p.get('text', '')}" for p in linkedin]
        blob = " ".join(texts).lower()
        words = [w for w in _WORD_RE.findall(blob) if w not in _STOPWORDS]
        top_kw = [w for w, _ in Counter(words).most_common(self.top_keywords)]

        # 3) Amazon : catégories d'achat
        cat_counts = Counter(
            r.get("category", "") for r in reviews if r.get("category")
        )
        top_cats = [c for c, _ in cat_counts.most_common(5) if c]

        # 4) LinkedIn : professionnel
        headline = linkedin[0].get("headline", "") if linkedin else ""
        skill_names = [s.get("name", "") for s in skills if s.get("name")][:8]
        professional = {}
        if headline or skill_names:
            professional = {"headline": headline, "skills": skill_names}

        # plateformes réellement présentes
        platforms = []
        if reddit_items:
            platforms.append("reddit")
        if reviews:
            platforms.append("amazon")
        if linkedin or skills:
            platforms.append("linkedin")

        interests = list(dict.fromkeys([*top_subs, *top_kw]))
        segments = (top_subs or top_cats)[:3]

        return {
            "user_hash": user_hash,
            "interests": interests,
            "needs": {"implicit": top_kw[:5]},
            "professional": professional,
            "consumption": {"preferred_categories": top_cats or top_subs[:5]},
            "marketing_segments": segments,
            "platforms_covered": platforms or ["reddit"],
            "profile_version": "heuristic",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
