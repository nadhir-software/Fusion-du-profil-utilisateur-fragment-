"""Démo : recommander de VRAIS items Amazon (dataset McAuley) à des personas.

Charge le catalogue Amazon Reviews 2023 (magazines), encode chaque item avec
Sentence-BERT, puis recommande les items les plus pertinents pour un profil
synthétique — un par persona. Aucune donnée réelle d'utilisateur ; le catalogue
provient d'un dataset public de recherche (≠ scraping).

Exécution : python scripts/reco_amazon_demo.py
"""

from __future__ import annotations


def main(
    category: str = "Magazine_Subscriptions", limit: int = 3000, top_k: int = 4
) -> None:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    from maha_these.core.anonymizer import DataAnonymizer
    from maha_these.data_generation.synthetic import SyntheticDataGenerator
    from maha_these.data_ingestion.amazon_reviews import download_category, load_catalog
    from maha_these.layer3_profile.heuristic_profile import HeuristicProfileBuilder
    from maha_these.layer4_recommendation.profile_encoder import ProfileEncoder

    # 1) Catalogue Amazon réel
    path = download_category(category)
    catalog = load_catalog(path, limit=limit)
    print(f"Catalogue Amazon '{category}' : {len(catalog)} items réels\n")

    # 2) Encodage du catalogue (une seule fois)
    encoder = ProfileEncoder()
    cat_emb = encoder.encode([f"{c['name']} {c['description']}" for c in catalog])

    # 3) Un utilisateur synthétique par persona
    gen = SyntheticDataGenerator(42)
    anonymizer = DataAnonymizer()
    builder = HeuristicProfileBuilder()
    from maha_these.data_generation.synthetic import PERSONAS

    persona_user: dict[str, str] = {}
    i = 0
    while len(persona_user) < len(PERSONAS) and i < 500:
        username = f"user_{i}"
        persona_user.setdefault(gen.persona(username)["name"], username)
        i += 1

    # 4) Recommandations réelles par persona
    for persona, username in persona_user.items():
        profile = builder.build(anonymizer.anonymize(gen.generate_all(username)), "h")
        prof_emb = encoder.encode_profiles([profile])
        sims = cosine_similarity(prof_emb, cat_emb)[0]
        top = np.argsort(sims)[::-1][:top_k]
        interests = ", ".join(profile["interests"][:4])
        print(f"=== persona '{persona}'  (intérêts : {interests}) ===")
        for j in top:
            print(f"   {sims[j]:.3f}  {catalog[j]['name'][:64]}")
        print()


if __name__ == "__main__":
    main()
