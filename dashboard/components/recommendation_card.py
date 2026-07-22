"""Composant carte de recommandation — affichage d'un item recommandé."""

from __future__ import annotations

from typing import Any


def recommendation_card(reco: dict[str, Any]) -> None:
    """Affiche une recommandation sous forme de carte Streamlit."""
    import streamlit as st

    with st.container(border=True):
        st.markdown(f"**#{reco.get('rank', '?')} — {reco.get('item_name', 'Item')}**")
        st.caption(f"Catégorie : {reco.get('category', 'n/a')}")
        score = reco.get("relevance_score")
        if score is not None:
            st.progress(min(max(float(score), 0.0), 1.0))
            st.caption(f"Pertinence : {score:.2%}")
        if reco.get("explanation"):
            st.write(reco["explanation"])
