# Dashboard React — Federated User Profiling

Interface React (Vite) pour l'API FastAPI. Quatre onglets : **Profil**,
**Recommandation**, **Ciblage Marketing**, **Évaluation**.

## Prérequis

- Node.js ≥ 18
- L'API FastAPI lancée en parallèle :

  ```bash
  uvicorn maha_these.layer5_api.main:app --reload   # http://localhost:8000
  ```

## Démarrer

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Le proxy Vite redirige `/api` et `/health` vers `http://localhost:8000`, donc
aucune configuration CORS n'est nécessaire en développement. (Le backend
autorise tout de même `localhost:5173` via CORS pour les setups sans proxy.)

## Build de production

```bash
npm run build      # génère frontend/dist/
npm run preview    # sert le build localement
```

## Structure

```
frontend/
├── index.html
├── vite.config.js          # plugin React + proxy vers l'API
├── package.json
└── src/
    ├── main.jsx            # point d'entrée React
    ├── App.jsx             # shell : header, statut API live, nav à onglets, footer
    ├── api.js              # client fetch de l'API
    ├── styles.css          # design system + thème clair/sombre
    └── components/
        ├── ui.jsx               # primitives : Icon (SVG), Spinner, Notice, EmptyState, Chips
        ├── ProfileTab.jsx
        ├── RecommendationTab.jsx
        ├── TargetingTab.jsx
        ├── EvaluationTab.jsx
        ├── RadarChart.jsx        # radar SVG (sans dépendance)
        └── RecommendationCard.jsx
```

## Design

Design system maison (variables CSS), **sans librairie UI ni icônes externes** :
icônes SVG inline (`ui.jsx`), thème clair/sombre automatique (`prefers-color-scheme`),
états de chargement (spinner), vides (`EmptyState`) et erreurs (`Notice`) unifiés,
indicateur d'état de l'API en direct dans l'en-tête.

> Rappel confidentialité : le dashboard ne fait que consommer l'API. Les
> données brutes ne sont jamais persistées (RAM only côté backend).
