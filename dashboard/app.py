"""Dashboard Streamlit — point d'entrée (4 onglets).

Lancement :
    streamlit run dashboard/app.py

Chaque onglet délègue son rendu à un module de ``dashboard/pages``.
"""

from __future__ import annotations

import streamlit as st

from dashboard.pages import ciblage, evaluation, profil, recommandation

st.set_page_config(page_title="Federated Profiling Dashboard", layout="wide")
st.title("Federated User Profiling — Dashboard")

tabs = st.tabs(
    ["Profil", "Recommandation", "Ciblage Marketing", "Évaluation"]
)

with tabs[0]:
    profil.render()
with tabs[1]:
    recommandation.render()
with tabs[2]:
    ciblage.render()
with tabs[3]:
    evaluation.render()
