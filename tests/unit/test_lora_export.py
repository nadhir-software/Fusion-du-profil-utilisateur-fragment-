"""Tests CRITIQUES — le TrainerOutput ne transporte QUE des Δθ (poids LoRA).

Vérifie l'invariant de confidentialité au niveau du modèle de données, sans
lancer un entraînement réel (pas de dépendance à la pile ML lourde).
"""

from maha_these.core.data_models import TrainerOutput


def test_trainer_output_carries_only_weights():
    """Aucun champ de données brutes / texte dans TrainerOutput."""
    output = TrainerOutput(
        agent_id="F1_reddit",
        lora_weights={"layer.q_proj": [0.1, 0.2]},
        dataset_size=100,
    )
    fields = set(output.model_dump().keys())
    assert "lora_weights" in fields
    assert "raw_data" not in fields
    assert "texts" not in fields
    assert "dataset" not in fields


def test_lora_export_roundtrip(tmp_path):
    """WeightsExporter sauvegarde puis recharge des Δθ à l'identique (torch)."""
    import pytest

    torch = pytest.importorskip("torch")
    from maha_these.layer2_federated.weights_exporter import WeightsExporter

    weights = {"w": torch.ones(4)}
    path = WeightsExporter.save(weights, tmp_path / "delta.pt")
    reloaded = WeightsExporter.load(path)
    assert torch.allclose(reloaded["w"], weights["w"])
