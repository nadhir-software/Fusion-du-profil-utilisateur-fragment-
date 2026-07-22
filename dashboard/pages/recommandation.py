"""Onglet Recommandation — recommandations personnalisées (Axe 1)."""

from __future__ import annotations

import json

import streamlit as st

from dashboard.components.recommendation_card import recommendation_card
from maha_these.layer3_profile.profile_store import ProfileStore
from maha_these.layer4_recommendation.marketing_engine import MarketingRecommender


def render() -> None:
    st.subheader("Recommandations utilisateur")
    user_hash = st.text_input("Hash utilisateur", key="reco_user_hash")
    catalog_file = st.file_uploader("Catalogue produits (JSON)", type="json")
    top_k = st.slider("Nombre de recommandations", 5, 20, 10)

    if st.button("Générer recommandations") and user_hash and catalog_file:
        profile = ProfileStore.load(user_hash)
        if not profile:
            st.warning("Profil introuvable.")
            return
        catalog = json.load(catalog_file)
        recos = MarketingRecommender().recommend_to_user(profile, catalog, top_k)
        for r in recos:
            recommendation_card(r)
