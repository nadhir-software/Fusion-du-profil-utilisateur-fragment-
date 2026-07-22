"""Test d'intégration — pipeline complet crawl -> profil (Phase 1/2).

Marqué ``skip`` tant que l'orchestration réelle n'est pas branchée. Sert de
squelette pour valider le bout-en-bout une fois les crawlers/trainers prêts.
"""

import pytest


@pytest.mark.skip(reason="Orchestration complète à brancher (Phase 1/2).")
def test_full_pipeline_end_to_end():
    # crawl (silo anonymisé) -> preprocess -> fragments -> train (Δθ)
    # -> FedAvg (θ_global) -> génération profil -> stockage
    raise NotImplementedError
