"""Tests du loader Amazon Reviews (parsing McAuley → catalogue), sans réseau."""

import json

from maha_these.data_ingestion.amazon_reviews import load_catalog


def test_load_catalog_parses_mcauley_meta(tmp_path):
    path = tmp_path / "meta.jsonl"
    records = [
        {
            "parent_asin": "A1",
            "title": "PC Gamer",
            "main_category": "Magazine Subscriptions",
            "features": ["gaming reviews"],
            "description": ["monthly"],
        },
        {
            "parent_asin": "A2",
            "title": "",
            "main_category": "X",
        },  # sans titre -> ignoré
        {
            "parent_asin": "A3",
            "title": "Cuisine at Home",
            "categories": ["Food"],
        },
    ]
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

    catalog = load_catalog(path)
    assert len(catalog) == 2  # l'item sans titre est écarté

    item = catalog[0]
    assert item["id"] == "A1"
    assert item["name"] == "PC Gamer"
    assert "gaming reviews" in item["description"]
    assert item["category"] == "Magazine Subscriptions"
    # repli sur categories[-1] quand main_category absent
    assert catalog[1]["category"] == "Food"


def test_load_catalog_limit(tmp_path):
    path = tmp_path / "meta.jsonl"
    path.write_text(
        "\n".join(
            json.dumps({"parent_asin": f"A{i}", "title": f"Mag {i}"}) for i in range(10)
        ),
        encoding="utf-8",
    )
    assert len(load_catalog(path, limit=3)) == 3


def test_load_catalog_skips_malformed_lines(tmp_path):
    path = tmp_path / "meta.jsonl"
    path.write_text(
        '{"parent_asin":"A1","title":"Good"}\n'
        "NOT JSON\n"
        "\n"
        '{"parent_asin":"A2","title":"Also good"}\n',
        encoding="utf-8",
    )
    assert len(load_catalog(path)) == 2


def test_stream_reviews(tmp_path):
    from maha_these.data_ingestion.amazon_reviews import stream_reviews

    path = tmp_path / "reviews.jsonl"
    recs = [
        {
            "user_id": "U1",
            "parent_asin": "A1",
            "rating": 5,
            "title": "great",
            "text": "loved",
        },
        {"user_id": "U2", "asin": "A2", "rating": 3, "title": "ok", "text": ""},
    ]
    path.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")

    out = list(stream_reviews(path))
    assert len(out) == 2
    assert out[0]["user_id"] == "U1" and out[0]["parent_asin"] == "A1"
    assert out[1]["parent_asin"] == "A2"  # repli sur 'asin'
    assert len(list(stream_reviews(path, max_records=1))) == 1


def test_build_profiles_from_reviews(tmp_path):
    from maha_these.core.session_buffer import SessionBuffer
    from maha_these.data_ingestion.review_profiles import build_profiles_from_reviews

    path = tmp_path / "reviews.jsonl"
    recs = [
        {
            "user_id": "U1",
            "parent_asin": "G1",
            "title": "PC Gamer",
            "text": "fps gaming graphics",
        }
        for _ in range(3)
    ]
    recs.append(
        {"user_id": "U2", "parent_asin": "C1", "title": "cooking", "text": "recipe"}
    )  # 1 avis < min_reviews -> exclu
    path.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")

    catalog_index = {
        "G1": {"name": "PC Gamer", "category": "gaming"},
        "C1": {"name": "Cuisine", "category": "cooking"},
    }
    profiles = build_profiles_from_reviews(
        path, catalog_index, max_records=100, max_users=10, min_reviews=3
    )

    assert len(profiles) == 1  # seul U1 a >= 3 avis
    profile = profiles[0]
    assert profile["platforms_covered"] == ["amazon"]
    assert "gaming" in profile["consumption"]["preferred_categories"]
    assert profile["interests"]  # mots-clés extraits des avis
    # RAM effacée après traitement (aucun buffer résiduel)
    assert SessionBuffer._registry == {}
