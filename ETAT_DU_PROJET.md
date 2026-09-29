# État du projet — situation actuelle (précise)

**Projet :** Fusion Fédérée de Profils Utilisateurs + Recommandation Marketing
**Doctorante :** Maha Rammeh · **Directeur :** Pr. Ahmed Hadj Kacem — ReDCAD, FSEG Sfax
**Package :** `maha_these` (installable, `src/` layout) · Python ≥ 3.11

> Ce document décrit **exactement** ce qui existe, ce qui tourne réellement, ce
> qui est prêt mais nécessite la pile ML, et ce qui reste à faire. Il complète
> `README.md` (démarrage rapide) et `RUNBOOK.md` (lancer le pipeline réel).

---

## 1. Résumé exécutif

Le système complet (5 couches) est **entièrement échafaudé et câblé de bout en
bout**. Le cœur non-ML (anonymisation, tampon RAM, orchestration, agrégation
FedAvg, API REST, store de profils, métriques, dashboard React) est
**fonctionnel et testé**. Les composants qui dépendent de la pile ML lourde
(entraînement LoRA sur Mistral-7B, embeddings Sentence-BERT, génération de
profil par LLM) sont **codés selon les API réelles** mais **non exécutés dans
cet environnement** (pas de GPU/torch/modèles ici).

**Statut global :** Phase 1 (multisources) terminée au niveau structure + tests ;
Phase 2/3 câblées, en attente d'exécution sur machine équipée (GPU + identifiants).

**Qualité :** `50 tests passent, 2 skippés` (les 2 skips = tests d'intégration
volontairement marqués skip ; les tests `torch` tournent désormais). `ruff` +
`black` clean. CI GitHub Actions en place.

**Mise à jour du 2026-07-24 :** `torch`, `transformers` et `sentence-transformers`
sont installés dans l'environnement. Le **moteur de recommandation est actif et
testé en live** (onglets Recommandation + Ciblage fonctionnels).

---

## 2. Principe fondateur — « ne pas enregistrer les data »

C'est **la** contrainte structurante du projet :

- Les données brutes collectées **ne sont jamais écrites sur disque** — ni base,
  ni CSV, ni JSON, ni cache. Elles transitent uniquement en **RAM** via
  `SessionBuffer`, isolé par session, effacé en fin de traitement.
- Les profils générés vivent aussi en **RAM** (`ProfileStore`, backend mémoire
  par défaut, ou Redis RAM-only pour le partage multi-process).
- Anonymisation **immédiate** dès la collecte (SHA-256 + masquage PII).
- Seuls **artefacts dérivés** quittent la session : les Δθ (poids LoRA) vers
  l'agrégateur, et le profil final anonymisé.
- Seul écriture disque autorisée : les **poids LoRA** dans `models/` (gitignoré).

Légende de statut utilisée ci-dessous :
- ✅ **Fonctionnel** sans pile ML (pur Python, testé/exécutable ici)
- ⚙️ **Code complet**, nécessite la pile lourde (`[ai]`/`[crawl]`) — non exécuté ici
- 🚧 **Stub** / à implémenter

---

## 3. Décisions d'architecture prises (journal)

| # | Décision | Raison |
|---|---|---|
| 1 | Code intégré dans le package `maha_these` (`src/`) au lieu d'un dossier `federated_user_profiling/` séparé | Rester un package installable, imports `from maha_these...` |
| 2 | **RAM only** : `SessionBuffer` remplace le stockage disque `LocalDataSilo` | Principe fondateur « ne pas enregistrer les data » |
| 3 | Profils **RAM only** (`ProfileStore` en mémoire) | Même principe, appliqué à la sortie |
| 4 | Dashboard en **React (Vite)** au lieu de Streamlit | Demande explicite ; front découplé de l'API |
| 5 | **Secure Aggregation** ajouté (FedAvg / FedProx / Secure / DP) | Aligné sur le diagramme d'architecture révisé |
| 6 | **OrchestrationAgent** (Workflow Manager) ajouté | Coordonne les crawlers dans une session RAM unique |
| 7 | `ProfileStore` = **façade à backend enfichable** (mémoire / Redis RAM-only) | Partager les profils entre CLI/API/workers sans disque |
| 8 | **Données synthétiques** (générateur multi-plateformes) pour la démo ; **pas de scraping Reddit/Amazon** | Conformité ToS Reddit/Amazon + RGPD ; données réelles = voie RFR Program + consentement |

---

## 4. Architecture par couche — statut module par module

### Couche cœur — `src/maha_these/core/`
| Module | Statut | Rôle |
|---|---|---|
| `base_agent.py` | ✅ | Interface abstraite `BaseAgent` |
| `data_models.py` | ✅ | Modèles Pydantic (Post, Comment, Fragment, TrainerOutput, UserProfile) |
| `anonymizer.py` | ✅ testé | SHA-256 + nettoyage PII (mentions/URLs/emails) |
| `session_buffer.py` | ✅ testé | **Tampon RAM** isolé par session, effacement garanti |
| `orchestrator.py` | ✅ testé | Coordonne les crawlers → un buffer RAM |

### Couche 1 — Crawling · `src/maha_these/layer1_crawling/`
| Module | Statut | Rôle |
|---|---|---|
| `base_crawler.py` | ✅ testé | Anonymise → pousse en RAM (jamais de disque) |
| `reddit_crawler.py` | ⚙️ | PRAW ; `crawl_user` réel — requiert `praw` + identifiants |
| `linkedin_crawler.py` | ⚙️ (parsing ✅ testé) | Playwright + BS4 ; helpers de parsing testés hors-ligne |
| `amazon_crawler.py` | ⚙️ (parsing ✅ testé) | Playwright + BS4 ; helpers de parsing testés hors-ligne |
| `rate_limiter.py` | ✅ | Token bucket |
| `mcp_client.py` | 🚧 | Client MCP générique (transport à brancher) |

### Couche 2 — Fragmentation fédérée · `src/maha_these/layer2_federated/`
| Module | Statut | Rôle |
|---|---|---|
| `preprocessor.py` | ✅ | Nettoyage/normalisation/filtrage ; `detect_language` optionnel |
| `system_prompts.py` | ✅ | Prompts spécialisés F1/F2/F3 |
| `fragment_builder.py` | ⚙️ | Dataset HuggingFace (requiert `datasets`) |
| `lora_config.py` | ⚙️ | Config PEFT/LoRA (requiert `peft`) |
| `trainer_agent.py` | ⚙️ | Entraînement LoRA local → Δθ (requiert transformers/peft/trl/torch) |
| `weights_exporter.py` | ⚙️ | Export/import des Δθ (requiert torch) |

### Couche 3 — Agrégation & profil · `src/maha_these/layer3_profile/`
| Module | Statut | Rôle |
|---|---|---|
| `aggregator.py` | ✅ testé (torch) | FedAvg/FedProx/**Secure**/DP — FedAvg numérique validé |
| `profile_generator.py` | ⚙️ | Génération profil JSON par inférence LLM |
| `profile_store.py` | ✅ testé | **Façade** : backend mémoire (défaut) ou **Redis RAM-only** |
| `profile_schemas.py` | ✅ | Schéma JSON du profil |

### Couche 4 — Recommandation · `src/maha_these/layer4_recommendation/`
| Module | Statut | Rôle |
|---|---|---|
| `profile_encoder.py` | ✅ actif | Embeddings Sentence-BERT (`all-mpnet-base-v2` installé) |
| `content_based.py` | ✅ testé live | Similarité cosinus profil ↔ items |
| `segment_clustering.py` | ✅ testé live | KMeans sur profils cibles (sklearn + ST) |
| `llm_recommender.py` | 🚧/⚙️ | Explications LLM (requiert modèle + tokenizer) |
| `marketing_engine.py` | ✅ actif | Façade Axe 1 (user) + Axe 2 (marketeur) |

### Couche 5 — API REST · `src/maha_these/layer5_api/`
| Élément | Statut | Rôle |
|---|---|---|
| `main.py` | ✅ | App FastAPI + CORS (React) |
| `routers/crawl.py` | ✅ endpoint (⚙️ tâche de fond) | `POST /crawl` → lance le pipeline, renvoie le `user_hash` |
| `routers/profile.py` | ✅ | `GET /profile/{hash}` |
| `routers/recommend.py` | ✅ testé live | `POST /recommend/user` + `/campaign` — embeddings réels |
| `routers/segments.py` | ✅ | `GET /profiles/segments` |
| `routers/evaluate.py` | ✅ (placeholder) | `GET /evaluate/comparison` |
| `routers/dev.py` | ✅ | `POST/DELETE /dev/seed` — profils de démo (DEV ONLY) |
| `schemas.py`, `dependencies.py` | ✅ | Validation Pydantic + injection |

### Orchestration bout-en-bout · `src/maha_these/pipeline.py`
✅ **câblage complet** `crawl → preprocess → fragment → train → aggregate →
profil → store` (effacement RAM garanti) — les étapes ML sont en import
paresseux (⚙️ non exécutées ici). Exposé via CLI (`scripts/run_pipeline.py`) et
via `POST /api/v1/crawl`.

### Évaluation scientifique · `evaluation/`
| Module | Statut |
|---|---|
| `metrics/profile_metrics.py` | precision@K ✅ · semantic_coherence ⚙️ · rouge_l ⚙️ |
| `metrics/reco_metrics.py` | ndcg@K ✅ · precision@K ✅ · davies_bouldin ⚙️ |
| `metrics/privacy_metrics.py` | ✅ (volume Δθ, ratio privacy/utility) |
| `baselines.py` | ✅ `fragment_plan` testé · `run_pipeline` câblé + **DP** (entraînement ⚙️) |
| `experiments/exp_01..05` | **les 5 runners ✅ testés** (entraînement ⚙️ ; EXP-03 utilise Sentence-BERT actif) |
| `mlflow_tracker.py` | ✅ wrapper (⚙️ requiert mlflow à l'usage) |

### Dashboard React · `frontend/`
✅ **compile** (`vite build` OK) · 4 onglets · client API · thème clair/sombre.
- Onglet **Profil** + vue segments : ✅ fonctionnent (avec profils en RAM).
- Onglets **Recommandation** / **Ciblage** : ✅ fonctionnent (Sentence-BERT
  installé, endpoints testés en live).

---

## 5. Ce qui tourne RÉELLEMENT ici vs ce qui nécessite une installation

**✅ Fonctionne maintenant (torch + transformers + sentence-transformers installés)**
- API REST complète (santé, profil, segments, evaluate, seed, **recommandation**)
- Anonymisation, tampon RAM, isolation de session, orchestration
- Agrégation FedAvg (numérique, **testée**), store de profils (mémoire + Redis)
- **Moteur de recommandation** : content-based + clustering (Sentence-BERT), testé live
- Dashboard React (build + 4 onglets : Profil, Reco, Ciblage, Évaluation)
- Métriques : precision@K, ndcg@K, privacy, cohérence sémantique

**⚙️ Reste à installer `pip install peft trl datasets accelerate`** (entraînement)
- Entraînement LoRA local + génération de profil par LLM (Mistral-7B)
- Métrique ROUGE (`rouge-score`)

**⚙️ Nécessite `pip install -e ".[crawl]"`** — crawling réel (+ identifiants Reddit)

**⚙️ Nécessite `pip install -e ".[crawl]"`** (praw, playwright, bs4)
- Crawling réel Reddit/LinkedIn/Amazon (+ `playwright install chromium` + identifiants)

**⚙️ Optionnel `pip install -e ".[redis]"`** — store de profils partagé multi-process

---

## 6. Le pipeline (schéma)

```
Requête ──► OrchestrationAgent
                 │  (collecte parallèle, 1 session RAM)
    ┌────────────┼────────────┐
 Reddit       LinkedIn      Amazon        ← anonymisation immédiate (SHA-256 + PII)
    └────────────┼────────────┘
                 ▼
          SessionBuffer (RAM only)         ← aucune écriture disque
                 ▼
  Preprocess → Fragment → TrainerAgent×N → Δθ
                 ▼
     FederatedAggregator (FedAvg/…) → θ_global
                 ▼
       ProfileGenerator (LLM) → profil JSON
                 ▼
        ProfileStore (RAM / Redis)  ──►  API  ──►  Dashboard React
                 │
          (buffer effacé — RAM wipe)
```

Lancer : voir **`RUNBOOK.md`** (installation, identifiants, `POST /crawl`, CLI).

---

## 7. Store de profils — mémoire vs Redis (RAM only)

| `PROFILE_STORE_BACKEND` | Partagé multi-process | Disque | Usage |
|---|---|---|---|
| `memory` (défaut) | ❌ local au process | aucun | dev, mono-process |
| `redis` | ✅ CLI + API + N workers | **aucun** (`--save "" --appendonly no`) | multi-workers |

Interface identique (`save/load/load_all/clear`) — aucun autre code à changer.
Détails : `RUNBOOK.md` §8.

---

## 8. Tests & qualité

- **50 tests passent, 2 skippés** (`pytest -q`). Les 2 skips = tests d'intégration
  volontairement marqués skip (pipeline complet / qualité reco). Les tests `torch`
  (FedAvg numérique, round-trip Δθ) passent désormais (torch installé).
- **Invariants de confidentialité couverts sans pile ML** : anonymisation (no PII),
  isolation/effacement du `SessionBuffer`, `TrainerOutput` ne porte que des Δθ,
  crawlers n'écrivent qu'en RAM, store RAM.
- `ruff` + `black` : clean. **CI** : `.github/workflows/ci.yml` (Python 3.11 + 3.12).

Fichiers de test : `tests/unit/` (anonymizer, session_buffer, orchestrator,
linkedin/amazon crawlers, fedavg, lora_export, api_endpoints, pipeline,
profile_store) + `tests/integration/` (skippés — pipeline complet / qualité reco).

---

## 9. Dépendances (extras)

```powershell
pip install -e .            # base : fastapi, pydantic, numpy, sklearn, pyyaml…
pip install -e ".[dev]"     # ruff, black, mypy, pytest, pytest-cov
pip install -e ".[ai]"      # torch, transformers, peft, trl, sentence-transformers…
pip install -e ".[crawl]"   # praw, playwright, beautifulsoup4
pip install -e ".[redis]"   # redis (store partagé RAM-only)
```
Frontend : `cd frontend && npm install` (Node ≥ 18).

---

## 10. Services (état d'exécution)

- **API FastAPI** — `uvicorn maha_these.layer5_api.main:app --reload` → http://localhost:8000 (`/docs` pour Swagger)
- **Dashboard React** — `cd frontend && npm run dev` → http://localhost:5173
- Seed de démo (dev) : `POST /api/v1/dev/seed` → hashes `demo_alice…demo_eva`

---

## 11. Correspondance avec le plan de thèse

| Phase | Plan | État réel |
|---|---|---|
| **0 — Fondation** | Reddit + LLM+LoRA+FedAvg + métriques | ✅ (structure) — exécution ML à relancer |
| **1 — Multisources** | Crawlers LinkedIn/Amazon, anonymiseur, silos, baselines, tests | ✅ crawlers + anonymiseur + **RAM** + tests ; baselines 🚧 |
| **2 — Reco + API** | Sentence-BERT, content-based, API 7 endpoints, dashboard, MLflow | ✅ API + dashboard React + **reco active** (Sentence-BERT, testée) ; MLflow wrapper ✅ |
| **3 — Science + Pub** | EXP-01..04, LLM matching, clustering, rédaction | ⚙️/🚧 câblé, à exécuter |

---

## 12. Ce qui reste à faire (par priorité)

1. **Exécuter le pipeline réel** sur machine GPU (RUNBOOK) : valider crawl→train→profil.
2. ~~Onglets Reco/Ciblage (sentence-transformers)~~ — ✅ **Fait** (installé, testé live).
3. ~~`evaluation/baselines.py` + EXP-01~~ — ✅ **Fait** (fragment_plan testé, harnais comparatif). Reste à exécuter avec l'entraînement réel.
4. ~~EXP-02/03/04/05~~ ✅ **Fait** — les 5 campagnes ont un runner testé ; DP câblé dans l'agrégation.
5. **Secure Aggregation** : brancher le protocole cryptographique réel (masquage par paires).
6. **`mcp_client.py`** : brancher le transport MCP (LinkedIn/Reddit).
7. ~~CI Node~~ ✅ **Fait** — job `frontend` (npm ci + `npm run build`) ajouté au workflow.
8. ~~Nettoyage `dashboard/` (Streamlit)~~ ✅ **Fait** — supprimé (remplacé par `frontend/` React).

---

*Dernière mise à jour reflétant l'état du code au commit courant. Voir aussi
`README.md`, `RUNBOOK.md`, `frontend/README.md`.*
