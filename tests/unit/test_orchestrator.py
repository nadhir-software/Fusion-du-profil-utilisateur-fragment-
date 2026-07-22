"""Tests OrchestrationAgent — collecte multi-plateformes en RAM + effacement."""

from maha_these.core.orchestrator import OrchestrationAgent
from maha_these.core.session_buffer import SessionBuffer


class _FakeCrawler:
    """Crawler factice qui écrit dans le buffer sans I/O réseau."""

    def __init__(self, platform: str) -> None:
        self.platform = platform

    def run(self, identifier, buffer=None):
        buffer.write(
            self.platform, {"user_hash": f"h_{self.platform}", "items": [identifier]}
        )
        return {"status": "success", "platform": self.platform}


def test_collect_multi_platform_in_ram():
    orch = OrchestrationAgent(
        {"reddit": _FakeCrawler("reddit"), "linkedin": _FakeCrawler("linkedin")}
    )
    # amazon absent des crawlers + cible vide -> ignoré
    buf = orch.collect({"reddit": "u1", "linkedin": "url1", "amazon": ""})
    try:
        assert set(buf.platforms()) == {"reddit", "linkedin"}
        assert buf.read("reddit")["user_hash"] == "h_reddit"
    finally:
        buf.clear()


def test_run_wipes_session():
    orch = OrchestrationAgent({"reddit": _FakeCrawler("reddit")})
    summary = orch.run({"reddit": "u1"})
    assert summary["status"] == "success"
    assert summary["platforms_collected"] == ["reddit"]
    # la session RAM a été vidée : plus rien dans le registre
    assert SessionBuffer.get(summary["session_id"]) is None
