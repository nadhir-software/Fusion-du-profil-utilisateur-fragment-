import { useState } from "react";
import { api } from "../api.js";
import RecommendationCard from "./RecommendationCard.jsx";
import { Icon, Spinner, Notice, EmptyState } from "./ui.jsx";

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
  const [catalog, setCatalog] = useState(null);

  async function generate() {
    setError("");
    setRecos(null);
    let parsed;
    try {
      parsed = JSON.parse(catalogText);
    } catch {
      setError("Catalogue JSON invalide.");
      return;
    }
    setLoading(true);
    try {
      const data = await api.recommendToUser(userHash, parsed, Number(topK));
      setRecos(data.recommendations || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function generateFromAmazon() {
    if (!userHash) return;
    setError("");
    setRecos(null);
    setLoading(true);
    try {
      const data = await api.recommendFromCatalog(userHash, Number(topK));
      setRecos(data.recommendations || []);
      if (data.catalog) setCatalog(data.catalog);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Recommandations utilisateur</h2>
      <p className="section-lead">
        Axe 1 — recommandation à l'utilisateur : le profil est encodé (Sentence-BERT)
        puis apparié par similarité cosinus au catalogue.
        {catalog?.size ? (
          <>
            {" "}
            Catalogue Amazon réel : <strong>{catalog.size}</strong> items
            {catalog.categories?.length
              ? ` (${catalog.categories.length} catégories)`
              : ""}
            .
          </>
        ) : null}
      </p>

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
        <button
          className="btn"
          onClick={generateFromAmazon}
          disabled={loading || !userHash}
        >
          {loading ? <Spinner /> : <Icon name="box" size={15} />}
          Catalogue Amazon (réel)
        </button>
      </div>

      <details className="details-toggle">
        <summary>Ou tester avec un catalogue JSON manuel</summary>
        <label className="field-label">Catalogue produits (JSON)</label>
        <textarea
          className="textarea"
          rows={8}
          value={catalogText}
          onChange={(e) => setCatalogText(e.target.value)}
        />
        <div className="row" style={{ marginTop: 10, marginBottom: 0 }}>
          <button
            className="btn secondary"
            onClick={generate}
            disabled={loading || !userHash}
          >
            {loading ? <Spinner /> : <Icon name="reco" size={15} />}
            Générer (JSON)
          </button>
        </div>
      </details>

      {error && <Notice kind="error">{error}</Notice>}

      {recos && recos.length === 0 && (
        <EmptyState icon="reco" title="Aucune recommandation">
          Le profil n'a produit aucun appariement au-dessus du seuil.
        </EmptyState>
      )}
      {recos && recos.length > 0 && (
        <div className="reco-list">
          {recos.map((r, i) => (
            <RecommendationCard key={r.item_id ?? i} reco={r} />
          ))}
        </div>
      )}
      {!recos && !error && (
        <EmptyState icon="box" title="Prêt à recommander">
          Saisissez un hash utilisateur, puis lancez sur le catalogue Amazon réel.
        </EmptyState>
      )}
    </section>
  );
}
