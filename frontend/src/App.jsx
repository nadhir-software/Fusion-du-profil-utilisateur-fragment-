import { useEffect, useState } from "react";
import { api } from "./api.js";
import { Icon } from "./components/ui.jsx";
import ProfileTab from "./components/ProfileTab.jsx";
import RecommendationTab from "./components/RecommendationTab.jsx";
import TargetingTab from "./components/TargetingTab.jsx";
import EvaluationTab from "./components/EvaluationTab.jsx";

const TABS = [
  { id: "profil", label: "Profil", icon: "profile", Component: ProfileTab },
  { id: "reco", label: "Recommandation", icon: "reco", Component: RecommendationTab },
  { id: "ciblage", label: "Ciblage Marketing", icon: "target", Component: TargetingTab },
  { id: "eval", label: "Évaluation", icon: "chart", Component: EvaluationTab },
];

function ApiStatus() {
  const [state, setState] = useState("checking"); // checking | up | down

  useEffect(() => {
    let alive = true;
    const ping = () =>
      api
        .health()
        .then(() => alive && setState("up"))
        .catch(() => alive && setState("down"));
    ping();
    const t = setInterval(ping, 15000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const label =
    state === "up" ? "API connectée" : state === "down" ? "API hors ligne" : "Connexion…";
  const dotClass = state === "up" ? "ok" : state === "down" ? "bad" : "pulse";

  return (
    <span className="status" title="État de l'API FastAPI (:8000)">
      <span className={`dot ${dotClass}`} />
      {label}
    </span>
  );
}

export default function App() {
  const [active, setActive] = useState("profil");
  const ActiveComponent = TABS.find((t) => t.id === active).Component;

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-logo">
            <Icon name="layers" size={24} />
          </span>
          <div className="brand-text">
            <h1>Federated User Profiling</h1>
            <p className="subtitle">
              Fusion fédérée de profils · Recommandation marketing
            </p>
          </div>
        </div>
        <div className="header-side">
          <span className="badge">
            <Icon name="lock" size={13} /> RAM only — aucune persistance
          </span>
          <ApiStatus />
        </div>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${active === t.id ? "active" : ""}`}
            onClick={() => setActive(t.id)}
          >
            <Icon name={t.icon} size={16} />
            {t.label}
          </button>
        ))}
      </nav>

      <main className="content">
        <ActiveComponent />
      </main>

      <footer className="app-footer">
        <span>ReDCAD · FSEG Sfax — Architecture fédérée 5 couches</span>
        <span>Δθ (LoRA) + profil anonymisé uniquement · SHA-256</span>
      </footer>
    </div>
  );
}
