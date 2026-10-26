import { useState } from "react";
import { api } from "../api.js";
import { Icon, Spinner, Notice, EmptyState } from "./ui.jsx";

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
      <p className="section-lead">
        Axe 2 — ciblage pour le marketeur : la campagne est encodée puis comparée à
        tous les profils du registre RAM pour identifier les segments les plus
        affinitaires.
      </p>

      <div className="card">
        <label className="field-label">Description de la campagne</label>
        <textarea
          className="textarea"
          rows={4}
          placeholder="Ex. : nouvelle gamme d'équipements de cyclisme haut de gamme pour sportifs d'endurance…"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <div className="row" style={{ marginTop: 12, marginBottom: 0 }}>
          <label className="inline" style={{ flex: 1, minWidth: 220 }}>
            Seuil d'affinité&nbsp;: <strong>{Number(threshold).toFixed(2)}</strong>
            <input
              type="range"
              min={0.3}
              max={0.9}
              step={0.05}
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              style={{ flex: 1 }}
            />
          </label>
          <button
            className="btn"
            onClick={findTargets}
            disabled={loading || !description}
          >
            {loading ? <Spinner /> : <Icon name="target" size={15} />}
            Identifier les segments
          </button>
        </div>
      </div>

      {error && (
        <div style={{ marginTop: 16 }}>
          <Notice kind="error">{error}</Notice>
        </div>
      )}

      {segments && (
        <div style={{ marginTop: 18 }}>
          <p className="muted">{analyzed} profil(s) analysé(s).</p>
          {segments.length === 0 ? (
            <EmptyState icon="target" title="Aucun segment au-dessus du seuil">
              Abaissez le seuil d'affinité ou peuplez le registre avec plus de profils.
            </EmptyState>
          ) : (
            <div className="grid-3">
              {segments.map((s) => (
                <div className="card metric" key={s.segment_id}>
                  <div className="metric-label">{s.segment_id}</div>
                  <div className="metric-value">{s.size}</div>
                  <div className="metric-sub">
                    profils · affinité {(s.avg_affinity * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!segments && !error && !loading && (
        <div style={{ marginTop: 18 }}>
          <EmptyState icon="target" title="Décrivez une campagne">
            Saisissez une description produit, puis identifiez les segments cibles.
          </EmptyState>
        </div>
      )}
    </section>
  );
}
