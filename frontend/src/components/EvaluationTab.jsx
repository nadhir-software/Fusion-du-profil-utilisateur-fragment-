import { useEffect, useState } from "react";
import { api } from "../api.js";
import { Spinner, Notice, EmptyState } from "./ui.jsx";

export default function EvaluationTab() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .comparison()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  const hasMetrics = data && data.metrics && Object.keys(data.metrics).length > 0;

  return (
    <section>
      <h2>Comparaison — Fédéré vs Centralisé vs Mono-source</h2>
      <p className="section-lead">
        Résultats des campagnes EXP-01..04 (validation H1 : le fédéré atteint une
        qualité comparable au centralisé, sans jamais centraliser les données).
      </p>

      {error && <Notice kind="error">{error}</Notice>}
      {!data && !error && (
        <p className="muted">
          <Spinner /> Chargement…
        </p>
      )}

      {data && data.status === "not_computed" && (
        <EmptyState icon="chart" title="Résultats non encore calculés">
          Lancez les campagnes sur GPU —{" "}
          <code>python scripts/run_all_experiments.py --mode real</code> — pour
          peupler ce tableau (métriques journalisées dans MLflow).
        </EmptyState>
      )}

      {hasMetrics && data.mode === "smoke" && (
        <Notice kind="error">
          Résultats en mode <strong>SMOKE</strong> — câblage uniquement, chiffres NON
          scientifiques. Relancez <code>--mode real</code> (GPU) pour de vrais résultats.
        </Notice>
      )}
      {hasMetrics && data.mode === "real" && (
        <Notice kind="ok">
          Campagne réelle (entraînement LoRA)
          {data.generated_at ? ` — ${data.generated_at.slice(0, 16).replace("T", " ")}` : ""}
          .
        </Notice>
      )}

      {hasMetrics && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Métrique</th>
                {(data.configs || []).map((c) => (
                  <th key={c}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.metrics).map(([metric, byConfig]) => (
                <tr key={metric}>
                  <td>{metric}</td>
                  {(data.configs || []).map((c) => (
                    <td key={c}>
                      {byConfig && byConfig[c] != null ? byConfig[c] : "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
