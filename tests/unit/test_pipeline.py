"""Tests du pipeline bout-en-bout — logique d'orchestration (hors pile ML).

Les étapes ML (fragment/train/aggregate/generate) sont surchargées pour
valider le câblage crawl → preprocess → ... → store + effacement RAM, sans
dépendre de torch/transformers.
"""

from types import SimpleNamespace

from maha_these.core.data_models import TrainerOutput
from maha_these.core.session_buffer import SessionBuffer
from maha_these.layer3_profile.profile_store import ProfileStore
from maha_these.pipeline import FederatedProfilingPipeline


class _FakeCrawler:
    def __init__(self, platform: str) -> None:
        self.platform = platform

    def run(self, identifier, buffer=None):
        buffer.write(
            self.platform,
            {
                "user_hash": f"h_{self.platform}",
                "posts": [
                    {"body": "j adore le machine learning le cyclisme et la photo"}
                ],
            },
        )
        return {"status": "success"}


class _NoMLPipeline(FederatedProfilingPipeline):
    """Pipeline dont les étapes ML sont remplacées par des doublures."""

    def _build_fragment(self, platform, texts, user_hash):
        return (["dataset"], SimpleNamespace(fragment_id=f"F_{platform}"))

    def _train_fragment(self, fragment_id, dataset):
        return TrainerOutput(
            agent_id=fragment_id, lora_weights={"w": 1.0}, dataset_size=10
        )

    def _aggregate(self, outputs):
        return {"w": 1.0}

    def _generate_profile(self, theta_global, user_hash, platforms):
        return {"user_hash": user_hash, "interests": ["ml"]}


def test_pipeline_wiring_populates_profile_and_wipes_ram():
    ProfileStore.clear()
    pipe = _NoMLPipeline(
        {"reddit": _FakeCrawler("reddit"), "amazon": _FakeCrawler("amazon")}
    )
    result = pipe.run({"reddit": "u1", "amazon": "url2", "linkedin": ""})

    assert result["status"] == "success"
    assert result["n_fragments"] == 2
    assert set(result["platforms"]) == {"reddit", "amazon"}

    # profil bien stocké en RAM, indexé par le hash unifié
    profile = ProfileStore.load(result["user_hash"])
    assert profile is not None
    assert set(profile["platforms_covered"]) == {"reddit", "amazon"}

    # aucune session RAM ne subsiste après le run (buffers effacés)
    assert SessionBuffer._registry == {}
    ProfileStore.clear()


def test_pipeline_no_data_when_targets_empty():
    ProfileStore.clear()
    pipe = _NoMLPipeline({"reddit": _FakeCrawler("reddit")})
    result = pipe.run({"reddit": "", "amazon": "", "linkedin": ""})
    assert result["status"] == "no_data"
    ProfileStore.clear()
