"""Tests HeuristicProfileBuilder — profil dérivé des signaux Reddit (sans LLM)."""

from maha_these.layer3_profile.heuristic_profile import HeuristicProfileBuilder

SESSION_DATA = {
    "user_hash": "h1",
    "posts": [
        {
            "title": "Best machine learning framework",
            "body": "pytorch tensorflow comparison",
            "subreddit": "MachineLearning",
        }
    ],
    "comments": [
        {"body": "cycling is great exercise", "subreddit": "cycling"},
        {"body": "more machine learning stuff", "subreddit": "MachineLearning"},
    ],
}


def test_build_extracts_subreddits_and_keywords():
    profile = HeuristicProfileBuilder().build(SESSION_DATA, "h1")

    assert profile["user_hash"] == "h1"
    assert profile["profile_version"] == "heuristic"
    assert profile["platforms_covered"] == ["reddit"]

    # subreddit le plus fréquent en tête des intérêts et des segments
    assert "MachineLearning" in profile["interests"]
    assert "MachineLearning" in profile["marketing_segments"]

    # mots-clés extraits (stopwords filtrés, 'machine'/'learning'/'pytorch')
    assert any(kw in profile["interests"] for kw in ("machine", "learning", "pytorch"))
    # les stopwords ne doivent pas apparaître
    assert "the" not in profile["interests"]
    assert "and" not in profile["interests"]


def test_build_handles_empty_data():
    profile = HeuristicProfileBuilder().build({"user_hash": "h2"}, "h2")
    assert profile["interests"] == []
    assert profile["marketing_segments"] == []
    assert profile["platforms_covered"] == ["reddit"]


def test_build_multiplatform():
    data = {
        "user_hash": "h3",
        "posts": [
            {
                "title": "cycling training",
                "body": "endurance ride",
                "subreddit": "cycling",
            }
        ],
        "reviews": [{"category": "sports", "text": "running shoes comfortable"}],
        "profile": [{"headline": "Coach sportif", "text": "nutrition coaching"}],
        "skills": [{"name": "Coaching"}, {"name": "Nutrition"}],
    }
    profile = HeuristicProfileBuilder().build(data, "h3")

    assert set(profile["platforms_covered"]) == {"reddit", "amazon", "linkedin"}
    assert "sports" in profile["consumption"]["preferred_categories"]
    assert profile["professional"]["headline"] == "Coach sportif"
    assert "Coaching" in profile["professional"]["skills"]
    assert "cycling" in profile["interests"]
