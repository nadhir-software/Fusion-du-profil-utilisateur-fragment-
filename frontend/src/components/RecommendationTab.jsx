import { useState } from "react";
import { api } from "../api.js";
import RecommendationCard from "./RecommendationCard.jsx";

const SAMPLE_CATALOG = JSON.stringify(
  [
    { id: "P1", name: "Casque audio", description: "sans fil", category: "audio" },
    { id: "P2", name: "Livre ML", description: "deep learning", category: "livres" },
  ],
  null,
  2
);

export default function RecommendationTab() {
  const [userHash, setUserHash] = useState("");
  const [catalogText, setCatalogText] = useState(SAMPLE_CATALOG);
  const [topK, setTopK] = useState(10);
  const [recos, setRecos] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function generate() {
    setError("");
    setRecos(null);
    let catalog;
    try {
      catalog = JSON.parse(catalogText);
    } catch {
      setError("Catalogue JSON invalide.");
      return;
    }
    setLoading(true);
    try {
      const data = await api.recommendToUser(userHash, catalog, Number(topK));
      setRecos(data.recommendations || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Recommandations utilisateur</h2>
      <div className="row">
        <input
          className="input"
          placeholder="Hash utilisateur"
          value={userHash}
          onChange={(e) => setUserHash(e.target.value)}
        />
        <label className="inline">
          Top-K
          <input
            type="number"
            className="input small"
            min={1}
            max={50}
            value={topK}
            onChange={(e) => setTopK(e.target.value)}
          />
        </label>
        <button className="btn" onClick={generate} disabled={loading || !userHash}>
          {loading ? "Génération…" : "Générer"}
        </button>
      </div>

      <label className="field-label">Catalogue produits (JSON)</label>
      <textarea
        className="textarea"
        rows={8}
        value={catalogText}
        onChange={(e) => setCatalogText(e.target.value)}
      />

      {error && <p className="error">{error}</p>}

      {recos && recos.length === 0 && <p className="muted">Aucune recommandation.</p>}
      {recos && recos.length > 0 && (
        <div className="reco-list">
          {recos.map((r, i) => (
            <RecommendationCard key={r.item_id ?? i} reco={r} />
          ))}
        </div>
      )}
    </section>
  );
}
