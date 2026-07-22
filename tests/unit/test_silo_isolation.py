"""Tests CRITIQUES — invariant d'isolation des silos locaux."""

from maha_these.core.local_silo import LocalDataSilo


def test_silo_not_shared_between_agents(tmp_path):
    """Chaque silo n'est accessible que par son propre agent."""
    silo_reddit = LocalDataSilo(
        "reddit", data={"user_hash": "u1"}, output_dir=tmp_path
    )
    silo_linkedin = LocalDataSilo(
        "linkedin", data={"user_hash": "u1"}, output_dir=tmp_path
    )
    assert silo_reddit.path != silo_linkedin.path
    assert not silo_reddit.can_read(silo_linkedin.path)  # isolation stricte
    assert silo_reddit.can_read(silo_reddit.path)


def test_silo_save_load_roundtrip(tmp_path):
    """Les données sauvegardées se rechargent à l'identique."""
    data = {"user_hash": "abc", "posts": [{"body": "hello"}]}
    silo = LocalDataSilo("reddit", data=data, output_dir=tmp_path)
    path = silo.save()
    assert path.exists()

    reloaded = LocalDataSilo("reddit", data={"user_hash": "abc"}, output_dir=tmp_path)
    assert reloaded.load() == data
