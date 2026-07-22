"""Onglet Profil — chargement et visualisation d'un profil (radar chart)."""

from __future__ import annotations

import streamlit as st

from dashboard.components.radar_chart import radar_chart
from maha_these.layer3_profile.profile_store import ProfileStore


def render() -> None:
    st.subheader("Profil utilisateur unifié")
    user_hash = st.text_input("Hash utilisateur")
    if st.button("Charger profil") and user_hash:
        profile = ProfileStore.load(user_hash)
        if not profile:
            st.warning("Profil introuvable.")
            return
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Centres d'intérêt**")
            radar_chart(profile.get("interests", []))
        with col2:
            st.markdown("**Profil professionnel**")
            st.json(profile.get("professional", {}))
        with col3:
            st.markdown("**Consommation**")
            st.json(profile.get("consumption", {}))
