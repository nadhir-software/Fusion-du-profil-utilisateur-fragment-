# Maha These — Fusion Fédérée de Profils Utilisateurs + Recommandation Marketing

Système de profilage utilisateur **fédéré** (multi-plateformes, préservant la
confidentialité) et de **recommandation marketing**, développé dans le cadre
d'une thèse de doctorat (Maha Rammeh · Pr. Ahmed Hadj Kacem · ReDCAD, FSEG Sfax).

Architecture en 5 couches : crawling multi-plateformes → fragmentation fédérée
(LLM + LoRA) → agrégation (FedAvg) & profil global → moteur de recommandation
→ API REST + dashboard.

> **Principe fondateur — ne pas enregistrer les données.** Les données
> collectées ne sont **jamais** écrites sur disque (ni base, ni CSV, ni JSON,
> ni cache). Elles transitent uniquement en RAM via un `SessionBuffer` isolé
> par session, sont anonymisées immédiatement (SHA-256 + masquage PII), et
> seuls des artefacts dérivés quittent la session : les Δθ (poids LoRA) vers
> l'agrégateur fédéré, et le profil final anonymisé.

## Mise en place

1. Créer l'environnement virtuel:

```powershell
"C:/Users/Nadhir bh/AppData/Local/Programs/Python/Python311/python.exe" -m venv .venv
```

2. Activer l'environnement:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Installer les dépendances:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

Pour la pile IA complète, installez aussi:

```powershell
pip install -r requirements-ai.txt
```

4. Enregistrer le noyau Jupyter:

```powershell
python -m ipykernel install --user --name maha_these --display-name "Python (maha_these)"
```

5. Lancer Jupyter Lab:

```powershell
jupyter lab
```

Pour les couches spécialisées, installez les extras correspondants :

```powershell
pip install -e ".[ai]"          # LLM + LoRA + FedAvg + Sentence-BERT
pip install -e ".[crawl]"       # PRAW + Playwright + BeautifulSoup
```

Le dashboard est une application **React (Vite)** dans `frontend/` — voir
`frontend/README.md` (`npm install` puis `npm run dev`).

## Architecture (5 couches)

Le code des couches vit dans le package installable `maha_these` :

- `src/maha_these/core/` — abstractions communes : `BaseAgent`,
  `OrchestrationAgent` (Workflow Manager), modèles Pydantic, `DataAnonymizer`
  (SHA-256 + nettoyage PII), et **`SessionBuffer`** (tampon RAM isolé par
  session — aucune écriture disque).
- `src/maha_these/layer1_crawling/` — **Couche 1** : crawlers Reddit /
  LinkedIn / Amazon, `RateLimiter`, client MCP. Chaque crawler anonymise
  immédiatement puis **stream** les données dans le `SessionBuffer` (RAM).
- `src/maha_these/layer2_federated/` — **Couche 2** : prétraitement,
  fragments HuggingFace, config LoRA, `TrainerAgent`, export des Δθ.
- `src/maha_these/layer3_profile/` — **Couche 3** : `FederatedAggregator`
  (FedAvg / FedProx / Secure Aggregation + DP), `ProfileGenerator`,
  `ProfileStore` (registre RAM).
- `src/maha_these/layer4_recommendation/` — **Couche 4** : encodeur
  Sentence-BERT, content-based, LLM matching, clustering de segments.
- `src/maha_these/layer5_api/` — **Couche 5** : application FastAPI et routeurs.

Autres répertoires (racine du dépôt) :

- `config/` — `config.yaml`, `platforms.yaml`, `experiments.yaml`.
- `evaluation/` — baselines, métriques, campagnes EXP-01..05, tracking MLflow.
- `frontend/` — dashboard **React + Vite** (4 onglets) consommant l'API REST.
- `tests/` — tests unitaires (dont invariants de confidentialité) + intégration.
- `data/` — **rien n'est persisté** : données brutes ET profils générés
  vivent uniquement en RAM (`SessionBuffer` + `ProfileStore` en mémoire) et
  sont effacés en fin de session.
- `models/` — modèle de base + poids LoRA (gitignorés — seuls artefacts disque).

### Lancer les services

```powershell
# API REST (port 8000)
uvicorn maha_these.layer5_api.main:app --reload

# Dashboard React (port 5173) — dans un autre terminal
cd frontend; npm install; npm run dev

# Tests
pytest
```

### Statut de développement

- **Phase 0** (réalisée) : pipeline Reddit LLM + LoRA + FedAvg, métriques.
- **Phase 1** (en cours) : crawlers LinkedIn/Amazon, baselines, tests
  d'isolation — voir la checklist du plan de développement.

Les modules dépendant de la pile ML lourde (crawling réel, entraînement,
inférence) sont des squelettes marqués `TODO` / `NotImplementedError` ; le
cœur (anonymisation, silos, agrégation, API, métriques) est fonctionnel.
