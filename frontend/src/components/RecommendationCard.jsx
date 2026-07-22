// Carte d'une recommandation d'item (Axe 1 — utilisateur).

export default function RecommendationCard({ reco }) {
  const score = typeof reco.relevance_score === "number" ? reco.relevance_score : null;
  return (
    <div className="card reco-card">
      <div className="reco-head">
        <span className="reco-rank">#{reco.rank ?? "?"}</span>
        <strong>{reco.item_name ?? "Item"}</strong>
      </div>
      <div className="muted">Catégorie : {reco.category ?? "n/a"}</div>
      {score !== null && (
        <div className="reco-score">
          <div className="bar">
            <div
              className="bar-fill"
              style={{ width: `${Math.min(Math.max(score, 0), 1) * 100}%` }}
            />
          </div>
          <span>{(score * 100).toFixed(1)}%</span>
        </div>
      )}
      {reco.explanation && <p className="reco-explain">{reco.explanation}</p>}
    </div>
  );
}
