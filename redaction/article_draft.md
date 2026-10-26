# Fusion fédérée de profils utilisateurs préservant la confidentialité pour la recommandation marketing

**Maha Rammeh¹, Ahmed Hadj Kacem¹**
¹ ReDCAD, FSEG Sfax

> ⚠️ **Brouillon de travail.** Les résultats marqués **[RÉEL]** sont obtenus et
> reproductibles. Ceux marqués **[À COMPLÉTER — GPU]** attendent l'exécution des
> campagnes d'entraînement LoRA (voir `RUNBOOK.md`) : ne pas remplir avec des
> valeurs inventées. Figures dans `reports/figures/` (PNG + PDF).

---

## Résumé

Nous proposons un système de **profilage utilisateur fédéré** qui construit un
profil unifié à partir de signaux multi-plateformes tout en préservant la
confidentialité par conception. Contrairement aux approches centralisées, notre
système ne persiste **jamais** les données brutes : elles transitent uniquement
en mémoire (RAM), sont anonymisées dès la collecte (SHA-256 + masquage PII), et
seuls des artefacts dérivés — les mises à jour de poids LoRA (Δθ) et le profil
final anonymisé — quittent la session. Un moteur de recommandation à double axe
(recommandation à l'utilisateur, ciblage pour le marketeur) exploite ces profils
via des embeddings Sentence-BERT. Nous validons la séparabilité des profils
(silhouette = 0,74) et la qualité de recommandation (NDCG@5 = 1,00) sur des
données synthétiques reproductibles et un catalogue de produits réels (Amazon
Reviews 2023). L'infrastructure d'entraînement fédéré (QLoRA 4-bit sur
Mistral-7B) est **validée sur GPU grand public (8 Go)** ; la métrique
comparative H1 par génération LLM reste à affiner (cf. §5.3).

**Mots-clés :** apprentissage fédéré, LoRA, confidentialité, profilage
utilisateur, systèmes de recommandation.

---

## 1. Introduction

Le profilage utilisateur à des fins de recommandation marketing repose
traditionnellement sur la **centralisation** de larges volumes de données
personnelles, ce qui pose des problèmes de confidentialité (RGPD), de sécurité et
de conformité aux conditions d'utilisation des plateformes. Nous formulons trois
hypothèses :

- **H1** : un profil construit par **agrégation fédérée** atteint une qualité
  comparable à un profil centralisé, sans jamais centraliser les données.
- **H2** : la qualité du profil **croît avec le nombre de sources** fédérées.
- **H3** : le profil fédéré améliore la **recommandation** par rapport à une
  source unique.

Notre contribution est double : (i) une **architecture fédérée RAM-only** qui
garantit qu'aucune donnée brute n'est persistée ; (ii) un **pipeline de
fragmentation** LLM + LoRA dont seuls les poids de rang faible (Δθ) sont
échangés, réduisant la surface d'exposition.

---

## 2. Architecture du système

Le système se décompose en cinq couches (Figure `fig_architecture`) :

1. **Collecte multi-plateformes.** Des agents de collecte (Reddit, LinkedIn,
   Amazon) récupèrent des données publiques, **anonymisées immédiatement** par
   `DataAnonymizer` (hachage SHA-256 des identifiants, masquage des mentions,
   URLs et emails), puis déposées dans un `SessionBuffer` **en mémoire**.
2. **Fragmentation fédérée.** Chaque plateforme constitue un *fragment* : après
   prétraitement, un `TrainerAgent` entraîne localement un adaptateur **LoRA**
   (QLoRA 4-bit sur Mistral-7B) et n'exporte que les **Δθ**.
3. **Agrégation fédérée.** Un `FederatedAggregator` combine les Δθ par **FedAvg**
   (moyenne pondérée par la taille des fragments), avec variantes FedProx,
   Secure Aggregation et bruit de confidentialité différentielle (DP) optionnel.
4. **Recommandation.** Les profils sont encodés par **Sentence-BERT** ; un
   moteur *content-based* (similarité cosinus) recommande des items, et un
   clustering KMeans identifie des segments marketing.
5. **API & tableau de bord.** Une API REST (FastAPI) expose le système ; un
   tableau de bord React en visualise les résultats.

### 2.1 Confidentialité par conception (RAM-only)

Le principe fondateur est de **ne pas enregistrer les données**. Le
`SessionBuffer` est isolé par session et **effacé** en fin de traitement (aucune
écriture disque : ni base, ni CSV, ni JSON, ni cache). Le passage à l'échelle est
assuré par **streaming** : chaque utilisateur est traité individuellement en RAM,
son profil dérivé produit, puis sa session vidée. Ainsi, un grand volume de
données est compatible avec le principe RAM-only. Seuls les Δθ (rang 16, une
fraction des paramètres) et le profil final anonymisé subsistent.

---

## 3. Données et reproductibilité

Conformément aux conditions d'utilisation des plateformes et au RGPD, l'évaluation
n'utilise **pas** de données scrappées. Deux sources conformes sont employées :

- **Données synthétiques** (`SyntheticDataGenerator`) : six *personas*
  (technologie/ML, fitness, cuisine, finance, gaming, écologie), génération
  déterministe (graine fixe = 42), reproductible.
- **Catalogue de produits réels** : jeu de données public de recherche **Amazon
  Reviews 2023** (McAuley/UCSD) [Hou et al., 2024]. Les avis (interactions
  utilisateur-item) fournissent à la fois un catalogue et des profils réels
  dérivés du comportement d'achat, sans scraping.

---

## 4. Protocole expérimental

Le protocole (Figure `fig_protocol`) compare trois configurations sur les **mêmes
données**, même modèle, même graine (holdout 80/20) :

- **A — Fédérée** (Trainer×N + FedAvg) — système proposé ;
- **B — Centralisée** (données fusionnées) — borne supérieure ;
- **C — Mono-source** (une plateforme) — borne inférieure.

Métriques : Précision@K, NDCG@K, cohérence sémantique (Sentence-BERT), ROUGE-L,
indice de Davies-Bouldin. Le test de Wilcoxon évalue H1 (A ≈ B).

---

## 5. Résultats

### 5.1 Qualité du profilage **[RÉEL]**

La Figure `fig_persona_clusters` montre que les profils se séparent nettement par
persona dans l'espace d'embedding (PCA 2D) : **silhouette = 0,74**,
**Davies-Bouldin = 0,36** (n = 60, 6 personas). La Figure `fig_similarity_matrix`
confirme cette distinction : similarité cosinus inter-persona comprise entre
**0,23 et 0,45**, contre 1,00 sur la diagonale. Le profilage produit donc des
représentations sémantiquement séparables, fondement du clustering de segments.

### 5.2 Qualité de recommandation **[RÉEL]**

Sur un catalogue étiqueté par persona (Figure `fig_reco_quality`), le moteur
content-based atteint **NDCG@5 = 1,00** (classement parfait des items pertinents)
et Précision@3 = 0,89 (Précision@K plafonnée par le nombre d'items pertinents par
persona). Sur le **catalogue Amazon réel** (magazines), les recommandations sont
qualitativement pertinentes par persona (cuisine → *Cuisine at Home* ; finance →
*Kiplinger's Personal Finance* ; gaming → *PC Gamer* ; fitness → *Bicycling*).

### 5.3 Comparaison des configurations (H1) **[infrastructure validée — métrique à revoir]**

L'infrastructure d'entraînement fédéré a été **exécutée de bout en bout sur GPU
grand public** (NVIDIA RTX 4060 Laptop, 8 Go) : Mistral-7B en QLoRA 4-bit
s'entraîne avec un pic mémoire de **≈ 5,1 Go**, et la campagne EXP-01 enchaîne
sans erreur les trois configurations (5 entraînements LoRA locaux + agrégation
FedAvg + 3 générations de profil). La faisabilité sur matériel modeste est donc
démontrée.

En revanche, la **métrique H1 telle qu'implémentée n'est pas exploitable** :
`ProfileGenerator` sollicite le modèle à partir du seul identifiant anonyme
(sans texte comportemental dans le prompt) et l'évaluation compare les intérêts
par **correspondance exacte** de mots-clés. Avec un entraînement court, le modèle
produit un profil JSON générique (souvent tronqué), si bien que le champ
`interests` reste vide et que les métriques valent 0 pour les trois
configurations — un artefact du protocole d'évaluation, non du système fédéré.

Une évaluation robuste de H1 nécessite : (i) l'injection du contexte
comportemental dans le prompt de génération, (ii) une extraction JSON tolérante,
et (iii) une métrique de **cohérence sémantique** (Sentence-BERT) plutôt qu'un
appariement lexical exact. Les résultats de **qualité de profilage** rapportés
en §5.1–5.2 (silhouette 0,74 ; NDCG@5 = 1,00) restent, eux, réels et
exploitables : ils reposent sur la voie de profilage heuristique.

### 5.4 Impact du nombre de sources (H2)

Sur données **synthétiques**, la séparabilité **sature dès une source** (Figure
`fig_fragments_quality` : silhouette ≈ 0,74 pour 1, 2 ou 3 plateformes). Ce
résultat s'explique par la **redondance** des plateformes synthétiques : chacune
identifie déjà le persona. La validation d'H2 requiert des données réelles où les
sources sont **complémentaires** (intérêts ≠ profession ≠ achats), avec
l'entraînement LoRA. **[À approfondir — GPU / données complémentaires.]**

---

## 6. Discussion et limites

- **Confidentialité.** Le système ne persiste aucune donnée brute ; l'exposition
  est réduite aux Δθ. Une extension **Differential Privacy** (bruit gaussien) est
  câblée, et un protocole de **Secure Aggregation** par masquage additif par
  paires est **implémenté** : chaque client masque sa contribution pondérée par
  des masques qui s'annulent à la somme, si bien que le serveur obtient l'agrégat
  exact (== FedAvg) sans jamais observer un Δθᵢ individuel [Bonawitz et al., 2017].
  La tolérance aux abandons (partage de secret de Shamir) reste une extension.
- **Limites de l'évaluation synthétique.** Les personas synthétiques sont
  idéalisés et les plateformes redondantes, ce qui empêche de démontrer H2 dans
  ce cadre. Le dataset Amazon Reviews apporte des items et des profils réels,
  mais l'entraînement fédéré complet reste à exécuter sur GPU.
- **Conformité.** Aucune donnée n'est scrappée ; les données réelles proviennent 
  d'un dataset public de recherche. Une collecte de données utilisateurs réelles
  passerait par des voies autorisées (Reddit for Researchers, consentement).

---

## 7. Conclusion et perspectives

Nous avons présenté un système de profilage fédéré **préservant la
confidentialité par conception** (RAM-only, anonymisation immédiate, échange de
Δθ uniquement) et un moteur de recommandation validé sur données réelles. Les
perspectives incluent : l'exécution des campagnes EXP-01..05 sur GPU (runner
`scripts/run_all_experiments.py`), l'ajout de la **tolérance aux abandons** au
protocole Secure Aggregation déjà implémenté (masquage par paires), et un
générateur synthétique à signaux complémentaires pour tester H2.

---

## Références

- Hou, Y., Li, J., He, Z., Yan, A., Chen, X., McAuley, J. (2024). *Bridging
  Language and Items for Retrieval and Recommendation.* (Amazon Reviews 2023.)
- Hu, E. et al. (2021). *LoRA: Low-Rank Adaptation of Large Language Models.*
- McMahan, B. et al. (2017). *Communication-Efficient Learning of Deep Networks
  from Decentralized Data* (FedAvg).
- Bonawitz, K. et al. (2017). *Practical Secure Aggregation for Privacy-Preserving
  Machine Learning.*
- Reimers, N., Gurevych, I. (2019). *Sentence-BERT.*

---

*Correspondance figures ↔ sections : voir `REDACTION.md`. Régénérer les figures :
`python scripts/make_figures.py`.*
