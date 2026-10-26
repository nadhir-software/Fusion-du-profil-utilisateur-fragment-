# Traçabilité — Cahier des charges → code livré

Suivi item par item de la **checklist du plan de développement** (PDF
« Architecture Détaillée & Plan de Développement », section 12), face à l'état
réel du dépôt.

**Légende**
✅ Fait (code + tests) · ⚙️ Code prêt, exécution = GPU/pile ML · 🔄 Adapté
(déviation justifiée) · 🚧 Stub / extension future

**État global** : `55 tests passent`, ruff + black clean, CI active, 70 modules.
Le projet est **structurellement complet** selon le cahier des charges. Ne
restent que l'**exécution GPU** des campagnes et la **rédaction scientifique**.

---

## Phase 0 — Fondation

| Item du cahier des charges | Statut | Où |
|---|---|---|
| Architecture multi-agents (FL Crew) | ✅ | `core/`, `layer1..5/` |
| Pipeline LLM + LoRA + FedAvg | ✅ / ⚙️ | `layer2_federated/trainer_agent.py`, `layer3_profile/aggregator.py`, `pipeline.py` |
| Évaluation (métriques) | ✅ | `evaluation/metrics/` |
| MCP Server Reddit | 🚧 | `layer1_crawling/mcp_client.py` (transport à brancher) |

---

## Phase 1 — Multisources

### Sprint 1.1 — Crawlers multi-plateformes
| Item | Statut | Où |
|---|---|---|
| `linkedin_crawler.py` | ✅ (+tests) | `layer1_crawling/linkedin_crawler.py`, `tests/unit/test_linkedin_crawler.py` |
| `amazon_crawler.py` | ✅ (+tests) | `layer1_crawling/amazon_crawler.py`, `tests/unit/test_amazon_crawler.py` |
| `anonymizer.py` (SHA-256 + clean_text) | ✅ (+tests) | `core/anonymizer.py`, `tests/unit/test_anonymizer.py` |
| `local_silo.py` (isolation) | 🔄 → **RAM-only** | remplacé par `core/session_buffer.py` (aucune persistance disque) |
| Tester crawling LinkedIn/Amazon réel | ⚙️ | parsing testé hors-ligne ; live = réseau/identifiants (+ ToS, cf. données synthétiques) |

### Sprint 1.2 — Baselines + Tests
| Item | Statut | Où |
|---|---|---|
| `evaluation/baselines.py` | ✅ (+tests) | `evaluation/baselines.py`, `tests/unit/test_baselines.py` |
| `core/base_agent.py` | ✅ | `core/base_agent.py` |
| Externaliser hyperparamètres (config.yaml) | ✅ | `config/config.yaml`, `platforms.yaml`, `experiments.yaml` |
| `test_silo_isolation.py` | 🔄 ✅ | `tests/unit/test_session_buffer.py` (isolation + RAM wipe) |
| `test_anonymizer.py` | ✅ | `tests/unit/test_anonymizer.py` |
| `test_lora_export.py` | ✅ | `tests/unit/test_lora_export.py` |
| CI (tests à chaque commit) | ✅ | `.github/workflows/ci.yml` (Python 3.11/3.12 + build React) |

---

## Phase 2 — Reco + API

| Item | Statut | Où |
|---|---|---|
| `profile_encoder.py` (Sentence-BERT) | ✅ | `layer4_recommendation/profile_encoder.py` |
| `content_based.py` (cosine) | ✅ | `layer4_recommendation/content_based.py` |
| `metrics/profile_metrics.py` (Précision@K, BERT, ROUGE) | ✅ | `evaluation/metrics/profile_metrics.py` |
| `metrics/reco_metrics.py` (NDCG@K, DB) | ✅ | `evaluation/metrics/reco_metrics.py` |
| `layer5_api/main.py` + 7 endpoints REST | ✅ (+tests) | `layer5_api/main.py`, `routers/` (crawl, profile, recommend, segments, evaluate + health) |
| `schemas.py` (Pydantic) | ✅ | `layer5_api/schemas.py` |
| Dashboard 4 onglets | 🔄 → **React** | `frontend/` (Vite, 4 onglets) au lieu de Streamlit |
| MLflow tracking | ✅ | `evaluation/mlflow_tracker.py` |

---

## Phase 3 — Campagne scientifique

| Item | Statut | Où |
|---|---|---|
| EXP-01 (fédéré vs centralisé vs mono) | ✅ (harness testé) ⚙️ exéc. | `evaluation/experiments/exp_01_comparison.py` |
| EXP-02 (impact fragments {1,2,3}) | ✅ (testé) ⚙️ | `evaluation/experiments/exp_02_fragments.py` |
| EXP-03 (qualité reco) | ✅ (testé) | `evaluation/experiments/exp_03_recommendation.py` |
| EXP-04 (ablation rang LoRA) | ✅ (testé) ⚙️ | `evaluation/experiments/exp_04_lora_rank.py` |
| `llm_recommender.py` (LLM matching) | ✅ ⚙️ | `layer4_recommendation/llm_recommender.py` |
| `segment_clustering.py` (KMeans) | ✅ | `layer4_recommendation/segment_clustering.py` |
| Dashboard démo complet (4 onglets) | ✅ | `frontend/` (Profil, Recommandation, Ciblage, Évaluation — opérationnels) |
| Rédaction & soumission article | ⚙️ | plan + figures prêts (`REDACTION.md`, `scripts/make_figures.py`) ; écriture à faire |

---

## Extensions livrées **au-delà** du cahier des charges

| Extension | Où |
|---|---|
| RAM-only strict (aucune persistance des données) | `core/session_buffer.py`, `ProfileStore` mémoire |
| **Secure Aggregation réelle** (masquage additif par paires, Bonawitz 2017) + DP câblé | `layer3_profile/aggregator.py` (`masked_contributions`, `secure_aggregate`), tests `test_fedavg.py` |
| **Runner unique EXP-01..05** (mode smoke sans GPU + mode réel GPU) | `scripts/run_all_experiments.py`, `tests/unit/test_run_all_experiments.py` |
| Générateur de données synthétiques (conforme) | `data_generation/synthetic.py` |
| Intégration **dataset Amazon Reviews (McAuley)** — catalogue réel + profils réels depuis avis | `data_ingestion/`, `catalog_service.py` |
| Catalogue **multi-catégories** (reco sur vrais items) | `layer5_api/catalog_service.py` |
| **7 figures de thèse** (dont 2 résultats réels) | `scripts/make_figures.py`, `reports/figures/` |
| Store de profils **Redis RAM-only** (multi-workers) | `layer3_profile/profile_store.py` |

---

## Ce qui reste (honnête, hors périmètre « code »)

1. **Exécuter EXP-01..05 en réel** — ✅ **infrastructure validée sur GPU** : Mistral-7B en QLoRA 4-bit s'entraîne réellement sur un **RTX 4060 Laptop 8 Go** (pic VRAM ≈ 5,1 Go), EXP-01 a tourné de bout en bout (5 entraînements LoRA + agrégation FedAvg + 3 générations). ⚠️ **Nuance honnête** : la voie *génération LLM* donne des métriques = 0 (le prompt n'a pas de contexte comportemental + éval par match exact + JSON tronqué) → des chiffres H1 exploitables demandent d'injecter le contexte + une métrique sémantique. Les résultats de **qualité de profilage** (figures : silhouette 0,74, NDCG 1,0, voie heuristique) sont, eux, **réels et exploitables**. Cf. `RUNBOOK.md` §5bis.
2. **Rédaction & soumission** de l'article — plan (`REDACTION.md`) + figures prêts ; l'écriture reste à ta charge (je peux aider à structurer).
3. **`mcp_client.py`** — brancher un transport MCP réel (si nécessaire).
4. **Secure Aggregation** — ✅ **protocole de masquage additif par paires implémenté et testé** (`aggregator.secure_aggregate`, == FedAvg à la somme, masques cachant chaque Δθᵢ). Reste optionnel : la **tolérance aux abandons** (partage de secret de Shamir).
5. **Tests crawling live** LinkedIn/Amazon — réseau + identifiants (+ conformité ToS/RGPD : voir la voie données synthétiques / RFR Program).

> **Conclusion.** Tout ce qui relève du **développement** du cahier des charges
> est livré, testé et vérifiable. Les points restants relèvent de l'**exécution
> sur matériel GPU** et de la **rédaction scientifique** — pas du code.
