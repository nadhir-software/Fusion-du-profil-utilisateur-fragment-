import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function EvaluationTab() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.comparison().then(setData).catch((e) => setError(e.message));
  }, []);

  return (
    <section>
      <h2>Comparaison : Fédéré vs Centralisé vs Mono-source</h2>
      {error && <p className="error">{error}</p>}
      {!data && !error && <p className="muted">Chargement…</p>}

      {data && data.status === "not_computed" && (
        <p className="muted">
          Résultats non encore calculés — lancez les campagnes EXP-01..04
          (MLflow) pour peupler ce tableau.
        </p>
      )}

      {data && (
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
            {Object.entries(data.metrics || {}).map(([metric, byConfig]) => (
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
      )}
    </section>
  );
}
