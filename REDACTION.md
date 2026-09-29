# Plan de rédaction — structuré autour des figures

Guide pour rédiger les chapitres méthodologie / architecture / résultats, en
s'appuyant sur les figures de `reports/figures/`. Chaque section indique la
figure, le message clé et les chiffres à reporter.

> ⚠️ **Honnêteté scientifique** : distinguer clairement les résultats **réels**
> (obtenus ici avec Sentence-BERT sur données synthétiques) des résultats
> **en attente** (nécessitant l'entraînement LoRA sur GPU). Ne jamais présenter
> les valeurs d'exemple comme des résultats.

---

## Chapitre — Architecture du système

**Figure : `fig_architecture`**

- Présenter les 5 couches (crawling → fragmentation fédérée → agrégation →
  recommandation → API/dashboard).
- Insister sur le **principe fondateur** : « ne pas enregistrer les data » —
  RAM only (`SessionBuffer`), anonymisation SHA-256 immédiate, seuls les Δθ
  (poids LoRA) et le profil anonymisé quittent la session.
- Détailler : `DataAnonymizer`, `SessionBuffer` (isolation par session),
  `TrainerAgent` (LoRA/QLoRA), `FederatedAggregator` (FedAvg/FedProx/Secure/DP).

**Point de conformité** (à mentionner en méthodologie) : la collecte de vraies
données Reddit/Amazon est soumise à leurs CGU + RGPD ; l'évaluation est menée
sur **données synthétiques reproductibles** (générateur multi-personas, seed
fixe). Voir `ETAT_DU_PROJET.md` (décision #8).

---

## Chapitre — Protocole expérimental

**Figure : `fig_protocol`**

- Découpage holdout 80/20, seed = 42 (reproductibilité).
- Trois configurations : A (fédéré, proposé), B (centralisé, baseline haute),
  C (mono-source, baseline basse) — même données, même modèle.
- Métriques : Précision@K, NDCG@K, cohérence-BERT, ROUGE-L, Davies-Bouldin.
- Hypothèses :
  - **H1** : le fédéré atteint une qualité ≈ centralisée (test de Wilcoxon).
  - **H2** : la qualité croît avec le nombre de sources fédérées.
  - **H3** : (recommandation) le profil fédéré améliore la reco vs mono-source.

---

## Chapitre — Résultats

### 1. Qualité du profilage (RÉEL)

**Figures : `fig_persona_clusters`, `fig_similarity_matrix`**

- `fig_persona_clusters` : les profils se séparent nettement par persona dans
  l'espace d'embedding. **Reporter : silhouette = 0.74, Davies-Bouldin = 0.36
  (n = 60, 6 personas).** Conclusion : le profilage produit des représentations
  sémantiquement séparables — fondement du clustering de segments.
- `fig_similarity_matrix` : similarité cosinus inter-persona. Diagonale = 1.00,
  hors-diagonale **0.23–0.45**. Conclusion : personas distincts et cohérents ;
  les paires les plus proches (finance/éco ≈ 0.45) restent bien séparées.

### 2. Qualité de recommandation (RÉEL)

**Figure : `fig_reco_quality`**

- Content-based (Sentence-BERT) sur un catalogue étiqueté par persona.
- **Reporter : NDCG@5 = 1.00 (classement parfait), P@3 = 0.89, P@5 = 0.56.**
- Note méthodologique : P@K est **plafonné** à (nb items pertinents)/K — ici 3
  items pertinents/persona → P@5 ≤ 0.60. Le NDCG (insensible à ce plafond)
  montre que les items pertinents sont classés en tête.
- **Catalogue RÉEL** (`scripts/reco_amazon_demo.py`) : le moteur recommande de
  vrais items du dataset **Amazon Reviews 2023 (McAuley/UCSD)** — 3000 magazines.
  Les recommandations sont sémantiquement pertinentes par persona (foodie →
  *Cuisine at Home* ; finance → *Kiplinger's Personal Finance* ; gamer →
  *PC Gamer* ; fitness → *Bicycling* ; éco → *Permaculture Magazine* ; tech →
  *IEEE Spectrum*). Démontre le moteur sur données produits réelles, sans scraping.

### 3. Comparaison des configurations (À REMPLIR)

**Figure : `fig_exp_comparison`** (actuellement **gabarit / valeurs d'EXEMPLE**)

- Ce graphique attend les **vrais résultats** des campagnes EXP-01 (fédéré vs
  centralisé vs mono-source), qui nécessitent l'entraînement LoRA (GPU + pile
  `[ai]`, cf. `RUNBOOK.md`). Le code de plot est prêt : remplacer le dict
  `example` par les métriques réelles.
- Rédiger cette section **après** l'entraînement ; y appliquer le test de
  Wilcoxon (H1).

### 4. Impact du nombre de sources (RÉEL — résultat nuancé)

**Figure : `fig_fragments_quality`**

- **Observation honnête** : sur données **synthétiques**, une seule source
  (Reddit) sature déjà les métriques (silhouette ≈ 0.74 dès 1 source ; NDCG@5 =
  1.00). Les plateformes synthétiques sont **redondantes** (chacune identifie
  déjà le persona), pas **complémentaires**.
- **Conséquence** : cette figure **ne valide pas H2** dans le cadre synthétique.
  À présenter comme une **limite de l'évaluation synthétique**, pas comme un
  résultat négatif du système.
- **Validation correcte d'H2** : nécessite des données réelles où les sources
  apportent des signaux complémentaires (intérêts Reddit ≠ profession LinkedIn
  ≠ achats Amazon), avec l'entraînement LoRA. À traiter en travaux futurs.

---

## Chapitre — Discussion & limites

- **Conformité & éthique** : pas de scraping des plateformes ; profils sur
  données synthétiques ; **catalogue d'items = dataset public de recherche**
  (Amazon Reviews 2023, McAuley/UCSD, ≠ scraping) ; voie conforme pour des
  données utilisateurs réelles = RFR Program + consentement (RGPD).
- **Citation du dataset** (à inclure en bibliographie) :
  > Yupeng Hou, Jiacheng Li, Zhankui He, An Yan, Xiusi Chen, Julian McAuley.
  > *Bridging Language and Items for Retrieval and Recommendation.* 2024.
  > (Amazon Reviews 2023 — https://amazon-reviews-2023.github.io/)
- **Limites de l'évaluation synthétique** : redondance inter-plateformes (H2 non
  démontrable), personas idéalisés.
- **Travaux futurs** : entraînement LoRA réel (EXP-01..05), générateur
  synthétique à signaux complémentaires, Secure Aggregation cryptographique,
  branchement MCP.

---

## Correspondance figures ↔ sections (récapitulatif)

| Figure | Section | Statut |
|---|---|---|
| `fig_architecture` | Architecture | diagramme |
| `fig_protocol` | Protocole | diagramme |
| `fig_persona_clusters` | Résultats §1 | **RÉEL** |
| `fig_similarity_matrix` | Résultats §1 | **RÉEL** |
| `fig_reco_quality` | Résultats §2 | **RÉEL** |
| `fig_exp_comparison` | Résultats §3 | **à remplir (GPU)** |
| `fig_fragments_quality` | Résultats §4 | **RÉEL (nuancé, ≠ H2)** |

Régénérer toutes les figures : `python scripts/make_figures.py`.
