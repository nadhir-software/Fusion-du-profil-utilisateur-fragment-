"""Composant radar chart — visualisation des centres d'intérêt."""

from __future__ import annotations

from typing import Sequence


def radar_chart(interests: Sequence[str]) -> None:
    """Affiche un radar des centres d'intérêt via Plotly dans Streamlit."""
    import plotly.graph_objects as go  # import paresseux
    import streamlit as st

    labels = list(interests)
    if not labels:
        st.caption("Aucun centre d'intérêt à afficher.")
        return

    # Score uniforme faute de pondération : à enrichir quand le profil
    # exposera des poids d'intérêt (Phase 2).
    values = [1.0] * len(labels)
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=labels, fill="toself"))
    fig.update_layout(
        polar={"radialaxis": {"visible": True, "range": [0, 1]}},
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
