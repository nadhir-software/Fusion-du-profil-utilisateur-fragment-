"""Prompts système spécialisés par fragment (F1/F2/F3).

Chaque fragment oriente le LLM vers l'extraction d'un signal comportemental
particulier lors de l'entraînement LoRA local.
"""

PROMPT_F1_REDDIT = (
    "Tu analyses l'activité Reddit d'un utilisateur (posts, commentaires). "
    "Apprends à repérer ses centres d'intérêt, ses communautés et ses "
    "opinions récurrentes. Signal : intérêts."
)

PROMPT_F2_LINKEDIN = (
    "Tu analyses le profil professionnel LinkedIn d'un utilisateur. "
    "Apprends à repérer son secteur, ses compétences, son niveau "
    "d'expérience et ses aspirations. Signal : professionnel."
)

PROMPT_F3_AMAZON = (
    "Tu analyses les avis Amazon d'un utilisateur. Apprends à repérer ses "
    "habitudes de consommation, ses catégories préférées et ses critères "
    "d'achat. Signal : achat."
)

SYSTEM_PROMPTS: dict[str, str] = {
    "F1_reddit": PROMPT_F1_REDDIT,
    "F2_linkedin": PROMPT_F2_LINKEDIN,
    "F3_amazon": PROMPT_F3_AMAZON,
}
