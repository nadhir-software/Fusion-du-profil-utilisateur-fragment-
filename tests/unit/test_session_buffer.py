"""Tests CRITIQUES — tampon mémoire (RAM only) & isolation par session.

Vérifie le principe fondateur : les données transitent uniquement en RAM,
sont isolées par session, et sont effacées explicitement — aucune persistance.
"""

from maha_these.core.session_buffer import SessionBuffer


def test_write_read_roundtrip():
    with SessionBuffer("s1") as buf:
        buf.write("reddit", {"user_hash": "u1", "posts": [{"body": "x"}]})
        assert buf.read("reddit")["user_hash"] == "u1"
        assert buf.read("linkedin") is None  # plateforme absente
        assert buf.platforms() == ["reddit"]


def test_session_isolation():
    a = SessionBuffer("A")
    b = SessionBuffer("B")
    try:
        a.write("reddit", {"user_hash": "ua"})
        assert b.read("reddit") is None  # B ne voit rien de A
        assert not a.can_access(b)  # isolation stricte inter-sessions
        assert a.can_access(a)
        assert SessionBuffer.get("A") is a
    finally:
        a.clear()
        b.clear()


def test_context_manager_wipes_on_exit():
    buf = SessionBuffer("wipe")
    with buf:
        buf.write("amazon", {"user_hash": "u"})
        assert buf.platforms() == ["amazon"]
    # à la sortie du bloc : mémoire effacée + retiré du registre
    assert buf.platforms() == []
    assert SessionBuffer.get("wipe") is None


def test_no_disk_persistence_api():
    """Le buffer n'expose AUCUNE API d'écriture disque (ni save, ni path)."""
    buf = SessionBuffer()
    try:
        assert not hasattr(buf, "save")
        assert not hasattr(buf, "path")
        assert not hasattr(buf, "load")
    finally:
        buf.clear()
