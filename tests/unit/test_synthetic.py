"""Tests du générateur de données synthétiques (déterminisme, formes, crawlers)."""

import json

from maha_these.core.session_buffer import SessionBuffer
from maha_these.data_generation.synthetic import (
    SyntheticDataGenerator,
    SyntheticRedditCrawler,
    build_synthetic_pipeline,
)


def test_generator_is_deterministic():
    g1 = SyntheticDataGenerator(42)
    g2 = SyntheticDataGenerator(42)
    assert g1.generate_reddit("alice") == g2.generate_reddit("alice")
    assert g1.persona("alice")["name"] == g2.persona("alice")["name"]


def test_reddit_shape():
    data = SyntheticDataGenerator(1).generate_reddit("bob", n_posts=3, n_comments=5)
    assert data["username"] == "bob"
    assert len(data["posts"]) == 3
    assert len(data["comments"]) == 5
    post = data["posts"][0]
    assert {"id", "title", "body", "subreddit", "score", "created_utc", "type"} <= set(
        post
    )
    assert post["type"] == "post"


def test_amazon_and_linkedin_shape():
    g = SyntheticDataGenerator(1)
    amz = g.generate_amazon("bob", n_reviews=4)
    assert len(amz["reviews"]) == 4
    assert {"product", "category", "rating", "text", "type"} <= set(amz["reviews"][0])

    lk = g.generate_linkedin("bob")
    assert lk["profile"][0]["headline"]
    assert len(lk["skills"]) >= 1


def test_generate_all_merges_platforms():
    alld = SyntheticDataGenerator(1).generate_all("carol")
    assert "posts" in alld and "reviews" in alld and "profile" in alld


def test_synthetic_crawler_writes_anonymized_to_buffer():
    crawler = SyntheticRedditCrawler()
    with SessionBuffer() as buf:
        result = crawler.run("dave", buffer=buf)
        assert result["status"] == "success"
        data = buf.read("reddit")
        assert data["user_hash"]
        assert "dave" not in json.dumps(data)  # username hashé, jamais en clair


def test_build_synthetic_pipeline_has_three_crawlers():
    pipe = build_synthetic_pipeline()
    assert set(pipe.orchestrator.crawlers.keys()) == {"reddit", "linkedin", "amazon"}
