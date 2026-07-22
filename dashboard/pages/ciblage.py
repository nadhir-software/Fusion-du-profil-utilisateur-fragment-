"""Onglet Ciblage marketeur — segments de profils cibles (Axe 2)."""

from __future__ import annotations

import streamlit as st

from maha_these.layer3_profile.profile_store import ProfileStore
from maha_these.layer4_recommendation.marketing_engine import MarketingRecommender


def render() -> None:
    st.subheader("Ciblage d'une campagne marketing")
    campaign_desc = st.text_area("Description de la campagne marketing")
    threshold = st.slider("Seuil d'affinité minimum", 0.3, 0.9, 0.5)

    if st.button("Identifier segments cibles") and campaign_desc:
        profiles = ProfileStore.load_all()
        campaign = {"description": campaign_desc}
        segments = MarketingRecommender().find_target_segments(
            campaign, profiles, threshold=threshold
        )
        if not segments:
            st.info("Aucun segment au-dessus du seuil.")
            return
        for s in segments:
            st.metric(
                s["segment_id"],
                f"{s['size']} profils",
                f"{s['avg_affinity']:.1%}",
            )
