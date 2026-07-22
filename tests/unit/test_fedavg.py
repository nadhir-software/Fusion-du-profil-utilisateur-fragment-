"""Tests — vérification de l'agrégation FedAvg (nécessite torch)."""

import pytest

from maha_these.core.data_models import TrainerOutput
from maha_these.layer3_profile.aggregator import FederatedAggregator

torch = pytest.importorskip("torch")


def test_fedavg_weighted_average():
    """θ_global = (n1/N)·Δθ1 + (n2/N)·Δθ2 (moyenne pondérée)."""
    output1 = TrainerOutput(
        agent_id="F1",
        lora_weights={"w": torch.ones(10)},
        dataset_size=100,
        training_loss=0.5,
    )
    output2 = TrainerOutput(
        agent_id="F2",
        lora_weights={"w": torch.zeros(10)},
        dataset_size=50,
        training_loss=0.3,
    )
    result = FederatedAggregator().aggregate([output1, output2])
    expected = (100 / 150) * torch.ones(10) + (50 / 150) * torch.zeros(10)
    assert torch.allclose(result["w"], expected)


def test_fedavg_requires_outputs():
    with pytest.raises(ValueError):
        FederatedAggregator().aggregate([])
