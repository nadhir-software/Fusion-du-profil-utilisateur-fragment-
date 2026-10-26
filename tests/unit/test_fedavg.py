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


def _sample_outputs():
    return [
        TrainerOutput(
            agent_id="F1", lora_weights={"w": torch.randn(64)}, dataset_size=100
        ),
        TrainerOutput(
            agent_id="F2", lora_weights={"w": torch.randn(64)}, dataset_size=50
        ),
        TrainerOutput(
            agent_id="F3", lora_weights={"w": torch.randn(64)}, dataset_size=30
        ),
    ]


def test_secure_aggregate_equals_fedavg():
    """Le masquage par paires s'annule : l'agrégat sécurisé == FedAvg."""
    outputs = _sample_outputs()
    fedavg = FederatedAggregator(method="fedavg").aggregate(outputs)
    secure = FederatedAggregator(method="secure").aggregate(outputs)
    assert torch.allclose(secure["w"], fedavg["w"], atol=1e-5)


def test_secure_masks_hide_individual_contributions():
    """Aucune contribution masquée yᵢ n'est égale à sa vraie valeur wᵢ·Δθᵢ."""
    outputs = _sample_outputs()
    aggregator = FederatedAggregator(method="secure")
    total = sum(o.dataset_size for o in outputs)
    masked, keys = aggregator.masked_contributions(outputs)

    for i, output in enumerate(outputs):
        true_weighted = (output.dataset_size / total) * output.lora_weights["w"]
        # le serveur voit `masked[i]`, qui diffère nettement de la vraie valeur
        assert not torch.allclose(masked[i]["w"], true_weighted, atol=1e-3)

    # ... mais la somme des masques est nulle (les masques s'annulent)
    stacked = torch.stack([m["w"] for m in masked])
    weighted_sum = sum((o.dataset_size / total) * o.lora_weights["w"] for o in outputs)
    assert torch.allclose(stacked.sum(dim=0), weighted_sum, atol=1e-5)


def test_secure_single_client_returns_its_weighted_value():
    """Avec un seul client, aucune paire : l'agrégat == sa contribution."""
    out = TrainerOutput(
        agent_id="F1", lora_weights={"w": torch.ones(8)}, dataset_size=10
    )
    secure = FederatedAggregator(method="secure").aggregate([out])
    assert torch.allclose(secure["w"], torch.ones(8))
