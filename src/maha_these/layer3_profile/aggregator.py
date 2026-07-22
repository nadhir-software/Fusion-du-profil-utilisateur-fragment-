"""FederatedAggregator — agrégation fédérée des Δθ (FedAvg / FedProx).

FedAvg : θ_global = Σ (nᵢ / N) · Δθᵢ  (moyenne pondérée par la taille des
jeux de données locaux). FedProx ajoute un terme proximal. Un utilitaire
optionnel ``add_dp_noise`` permet d'ajouter du bruit gaussien (DP).

L'agrégateur ne reçoit QUE des ``TrainerOutput`` (Δθ) : jamais de données
brutes — invariant vérifié par tests/unit/test_fedavg.py.
"""

from __future__ import annotations

from typing import Iterable, Literal

from maha_these.core.data_models import TrainerOutput

Method = Literal["fedavg", "fedprox"]


class FederatedAggregator:
    """Agrège les poids LoRA locaux en un θ_global."""

    def __init__(self, method: Method = "fedavg", mu: float = 0.01) -> None:
        self.method = method
        self.mu = mu  # coefficient proximal pour FedProx

    def aggregate(self, outputs: Iterable[TrainerOutput]) -> dict:
        """Renvoie le dictionnaire de poids agrégés θ_global."""
        outputs = list(outputs)
        if not outputs:
            raise ValueError("aggregate() requiert au moins un TrainerOutput.")

        total = sum(o.dataset_size for o in outputs)
        if total <= 0:
            raise ValueError("La somme des tailles de datasets doit être > 0.")

        keys = outputs[0].lora_weights.keys()
        aggregated: dict = {}
        for key in keys:
            fedavg = sum(
                (o.dataset_size / total) * o.lora_weights[key] for o in outputs
            )
            if self.method == "fedprox":
                import torch  # import paresseux (terme proximal)

                prox = self.mu / 2 * torch.norm(fedavg) ** 2
                fedavg = fedavg - prox
            aggregated[key] = fedavg
        return aggregated

    def add_dp_noise(self, weights: dict, sigma: float = 0.1) -> dict:
        """Extension optionnelle : Differential Privacy sur θ_global."""
        import torch  # import paresseux

        if sigma <= 0:
            return weights
        return {k: v + torch.randn_like(v) * sigma for k, v in weights.items()}
