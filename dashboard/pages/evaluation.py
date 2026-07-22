"""Onglet Évaluation scientifique — comparaison des configurations."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.subheader("Comparaison : Fédéré vs Centralisé vs Mono-source")
    st.caption(
        "Les résultats proviennent des campagnes EXP-01..04 (MLflow). "
        "TODO(Phase 3) : brancher la lecture des runs MLflow."
    )
    # TODO(Phase 3): charger les métriques via l'API /evaluate/comparison
    # puis afficher un bar chart comparatif (une barre par config/métrique).
    st.info("Résultats non encore calculés.")
