import { useState } from "react";
import { api } from "../api.js";

export default function TargetingTab() {
  const [description, setDescription] = useState("");
  const [threshold, setThreshold] = useState(0.5);
  const [segments, setSegments] = useState(null);
  const [analyzed, setAnalyzed] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function findTargets() {
    if (!description) return;
    setError("");
    setSegments(null);
    setLoading(true);
    try {
      const data = await api.findCampaignTargets(description, Number(threshold));
      setSegments(data.segments || []);
      setAnalyzed(data.total_profiles_analyzed || 0);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Ciblage d'une campagne marketing</h2>
      <label className="field-label">Description de la campagne</label>
      <textarea
        className="textarea"
        rows={4}
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="row">
        <label className="inline">
          Seuil d'affinité : {Number(threshold).toFixed(2)}
          <input
            type="range"
            min={0.3}
            max={0.9}
            step={0.05}
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
          />
        </label>
        <button className="btn" onClick={findTargets} disabled={loading || !description}>
          {loading ? "Analyse…" : "Identifier les segments"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {segments && (
        <>
          <p className="muted">{analyzed} profil(s) analysé(s).</p>
          {segments.length === 0 ? (
            <p className="muted">Aucun segment au-dessus du seuil.</p>
          ) : (
            <div className="grid-3">
              {segments.map((s) => (
                <div className="card metric" key={s.segment_id}>
                  <div className="metric-label">{s.segment_id}</div>
                  <div className="metric-value">{s.size} profils</div>
                  <div className="metric-sub">
                    affinité {(s.avg_affinity * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
