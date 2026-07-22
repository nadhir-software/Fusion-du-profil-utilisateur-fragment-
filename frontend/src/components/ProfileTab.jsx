import { useState } from "react";
import { api } from "../api.js";
import RadarChart from "./RadarChart.jsx";

export default function ProfileTab() {
  const [userHash, setUserHash] = useState("");
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function load() {
    if (!userHash) return;
    setLoading(true);
    setError("");
    setProfile(null);
    try {
      setProfile(await api.getProfile(userHash));
    } catch (e) {
      setError(e.message.includes("404") ? "Profil introuvable." : e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2>Profil utilisateur unifié</h2>
      <div className="row">
        <input
          className="input"
          placeholder="Hash utilisateur"
          value={userHash}
          onChange={(e) => setUserHash(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <button className="btn" onClick={load} disabled={loading}>
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
