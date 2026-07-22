import { useState } from "react";
import ProfileTab from "./components/ProfileTab.jsx";
import RecommendationTab from "./components/RecommendationTab.jsx";
import TargetingTab from "./components/TargetingTab.jsx";
import EvaluationTab from "./components/EvaluationTab.jsx";

const TABS = [
  { id: "profil", label: "Profil", Component: ProfileTab },
  { id: "reco", label: "Recommandation", Component: RecommendationTab },
  { id: "ciblage", label: "Ciblage Marketing", Component: TargetingTab },
  { id: "eval", label: "Évaluation", Component: EvaluationTab },
];

export default function App() {
  const [active, setActive] = useState("profil");
  const ActiveComponent = TABS.find((t) => t.id === active).Component;

  return (
    <div className="app">
      <header className="app-header">
        <h1>Federated User Profiling</h1>
        <p className="subtitle">
          Fusion fédérée de profils · Recommandation marketing ·{" "}
          <span className="badge">RAM only — aucune persistance des données</span>
        </p>
      </header>

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${active === t.id ? "active" : ""}`}
            onClick={() => setActive(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="content">
        <ActiveComponent />
      </main>
    </div>
  );
}
