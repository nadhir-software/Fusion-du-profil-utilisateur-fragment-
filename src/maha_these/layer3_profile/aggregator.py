"""FederatedAggregator — agrégation fédérée sécurisée des Δθ.

Méthodes (cf. diagramme « Secure Federated Aggregation ») :
- ``fedavg``  : θ_global = Σ (nᵢ / N) · Δθᵢ (moyenne pondérée).
- ``fedprox`` : FedAvg + terme proximal (pénalise la divergence).
- ``secure``  : agrégation sécurisée — masquage additif qui s'annule à la
  somme, de sorte que l'agrégateur ne voit jamais un Δθᵢ individuel.

En complément, ``add_dp_noise`` applique une confidentialité différentielle
(bruit gaussien) optionnelle sur θ_global.

L'agrégateur ne reçoit QUE des ``TrainerOutput`` (Δθ) : jamais de données
brutes — invariant vérifié par tests/unit/test_fedavg.py.
"""

from __future__ import annotations

import hashlib
from typing import Iterable, Literal

from maha_these.core.data_models import TrainerOutput

Method = Literal["fedavg", "fedprox", "secure"]


class FederatedAggregator:
    """Agrège les poids LoRA locaux en un θ_global."""

    def __init__(
        self, method: Method = "fedavg", mu: float = 0.01, seed: int = 1234
    ) -> None:
        self.method = method
        self.mu = mu  # coefficient proximal pour FedProx
        self.seed = seed  # graine du PRG des masques (Secure Aggregation)

    def aggregate(self, outputs: Iterable[TrainerOutput]) -> dict:
        """Renvoie le dictionnaire de poids agrégés θ_global."""
        outputs = list(outputs)
        if not outputs:
            raise ValueError("aggregate() requiert au moins un TrainerOutput.")

        if self.method == "secure":
            return self.secure_aggregate(outputs)

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

    # ----------------------------------------------------------------- #
    # Secure Aggregation — masquage additif par paires (Bonawitz et al.)
    # ----------------------------------------------------------------- #
    def _pairwise_seed(self, i: int, j: int, key: str) -> int:
        """Graine partagée du masque de la paire (i, j) pour le tenseur ``key``.

        Dans un vrai déploiement, cette graine est le secret commun issu d'un
        accord de clés Diffie-Hellman entre les clients i et j ; le serveur ne
        la connaît jamais. Ici on la dérive de façon déterministe (SHA-256)
        pour rendre le protocole reproductible et testable.
        """
        digest = hashlib.sha256(f"{self.seed}:{i}:{j}:{key}".encode()).hexdigest()
        return int(digest[:15], 16)  # 60 bits — tient dans un int64

    def masked_contributions(
        self, outputs: Iterable[TrainerOutput], total: int | None = None
    ) -> tuple[list[dict], list[str]]:
        """Contributions **masquées** que chaque client envoie au serveur.

        Chaque client i pondère son Δθᵢ (wᵢ = nᵢ/N) puis y ajoute, pour chaque
        paire (i, j), un masque pseudo-aléatoire mₖ(i,j) : le client d'indice le
        plus faible l'**ajoute**, l'autre le **soustrait**. Les masques
        s'annulent donc à la somme (Σᵢ yᵢ = Σᵢ wᵢ·Δθᵢ), mais aucune contribution
        individuelle yᵢ ne révèle Δθᵢ en clair. Retourne ``(yᵢ, clés)``.
        """
        import torch  # import paresseux

        outputs = list(outputs)
        if total is None:
            total = sum(o.dataset_size for o in outputs)
        if total <= 0:
            raise ValueError("La somme des tailles de datasets doit être > 0.")

        keys = list(outputs[0].lora_weights.keys())
        n = len(outputs)
        # contributions pondérées wᵢ·Δθᵢ (clonées : on ne mute pas les entrées)
        masked = [
            {k: (o.dataset_size / total) * o.lora_weights[k].clone() for k in keys}
            for o in outputs
        ]
        # masques par paires : i ajoute, j (>i) soustrait → s'annulent à la somme
        for i in range(n):
            for j in range(i + 1, n):
                for key in keys:
                    ref = masked[i][key]
                    gen = torch.Generator().manual_seed(self._pairwise_seed(i, j, key))
                    mask = torch.randn(
                        ref.shape, generator=gen, dtype=torch.float64
                    ).to(dtype=ref.dtype, device=ref.device)
                    masked[i][key] = masked[i][key] + mask
                    masked[j][key] = masked[j][key] - mask
        return masked, keys

    def secure_aggregate(self, outputs: Iterable[TrainerOutput]) -> dict:
        """Agrégation sécurisée (Secure Aggregation).

        Chaque client masque sa contribution pondérée par des masques par
        paires qui s'annulent à la somme (cf. ``masked_contributions``). Le
        serveur ne fait qu'**additionner** les contributions masquées : il
        obtient l'agrégat exact (== FedAvg) sans jamais observer un Δθᵢ en
        clair. Cf. Bonawitz et al., 2017.

        Limite connue : cette version suppose qu'aucun client n'abandonne en
        cours de tour. La tolérance aux abandons (récupération des masques par
        partage de secret de Shamir) est une extension directe.
        """
        outputs = list(outputs)
        if not outputs:
            raise ValueError("secure_aggregate() requiert au moins un TrainerOutput.")
        masked, keys = self.masked_contributions(outputs)
        aggregated: dict = {}
        for key in keys:
            acc = None
            for contribution in masked:  # somme côté serveur (masques annulés)
                acc = contribution[key] if acc is None else acc + contribution[key]
            aggregated[key] = acc
        return aggregated
