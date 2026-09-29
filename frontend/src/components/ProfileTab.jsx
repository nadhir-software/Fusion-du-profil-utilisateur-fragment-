import { useState } from "react";
import { api } from "../api.js";
import RadarChart from "./RadarChart.jsx";

export default function ProfileTab() {
  const [userHash, setUserHash] = useState("");
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [redditUser, setRedditUser] = useState("");
  const [crawling, setCrawling] = useState(false);
  const [info, setInfo] = useState("");

  async function load(hash = userHash) {
    if (!hash) return;
    setLoading(true);
    setError("");
    setProfile(null);
    try {
      setProfile(await api.getProfile(hash));
    } catch (e) {
      setError(e.message.includes("404") ? "Profil introuvable." : e.message);
    } finally {
      setLoading(false);
    }
  }

  async function crawlReddit() {
    if (!redditUser) return;
    setCrawling(true);
    setError("");
    setInfo("");
    try {
      const res = await api.buildRedditProfile(redditUser, 100);
      setInfo(
        `Profil généré depuis Reddit : ${res.n_items} éléments · ` +
          `${res.interests.length} intérêts. Hash : ${res.user_hash}`
      );
      setUserHash(res.user_hash);
      await load(res.user_hash);
    } catch (e) {
      setError(e.message);
    } finally {
      setCrawling(false);
    }
  }

  return (
    <section>
      <h2>Profil utilisateur unifié</h2>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3>Analyser un profil Reddit réel</h3>
        <p className="muted">
          Crawl API Reddit → profil heuristique (subreddits + mots-clés). Nécessite
          les identifiants dans <code>.env</code>.
        </p>
        <div className="row">
          <input
            className="input"
            placeholder="pseudo Reddit (ex. spez)"
            value={redditUser}
            onChange={(e) => setRedditUser(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && crawlReddit()}
          />
          <button className="btn" onClick={crawlReddit} disabled={crawling}>
            {crawling ? "Analyse…" : "Analyser Reddit"}
          </button>
        </div>
        {info && <p className="muted">{info}</p>}
      </div>

      <div className="row">
        <input
          className="input"
          placeholder="Hash utilisateur"
          value={userHash}
          onChange={(e) => setUserHash(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <button className="btn" onClick={() => load()} disabled={loading}>
          {loading ? "Chargement…" : "Charger le profil"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {profile && (
        <div className="grid-3">
          <div className="card">
            <h3>Centres d'intérêt</h3>
            <RadarChart labels={profile.interests || []} />
          </div>
          <div className="card">
            <h3>Profil professionnel</h3>
            <pre className="json">
              {JSON.stringify(profile.professional || {}, null, 2)}
            </pre>
          </div>
          <div className="card">
            <h3>Consommation</h3>
            <pre className="json">
              {JSON.stringify(profile.consumption || {}, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </section>
  );
}
