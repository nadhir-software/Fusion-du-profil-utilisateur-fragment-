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
    ├── App.jsx             # navigation par onglets
    ├── api.js              # client fetch de l'API
    ├── styles.css          # thème clair/sombre
    └── components/
        ├── ProfileTab.jsx
        ├── RecommendationTab.jsx
        ├── TargetingTab.jsx
        ├── EvaluationTab.jsx
        ├── RadarChart.jsx        # radar SVG (sans dépendance)
        └── RecommendationCard.jsx
```

> Rappel confidentialité : le dashboard ne fait que consommer l'API. Les
> données brutes ne sont jamais persistées (RAM only côté backend).
