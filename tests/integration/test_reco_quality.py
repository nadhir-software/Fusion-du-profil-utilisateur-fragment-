"""Test d'intégration — qualité de la recommandation (Phase 2/3).

Marqué ``skip`` tant que l'encodeur Sentence-BERT et un catalogue de test ne
sont pas disponibles hors ligne.
"""

import pytest


@pytest.mark.skip(reason="Nécessite l'encodeur Sentence-BERT + catalogue (Phase 2/3).")
def test_content_based_top_k_size():
    # profil + catalogue -> recommend(top_k) -> len == top_k, scores dans [0,1]
    raise NotImplementedError
