import { useEffect, useState } from "react";
import { api } from "../api.js";
import RadarChart from "./RadarChart.jsx";
import { Icon, Spinner, Notice, EmptyState, Chips } from "./ui.jsx";

const short = (h) => (h && h.startsWith("demo_") ? h : `${(h || "").slice(0, 10)}…`);
const PAGE_SIZE = 60;

export default function ProfileTab() {
  const [userHash, setUserHash] = useState("");
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [redditUser, setRedditUser] = useState("");
  const [crawling, setCrawling] = useState(false);
  const [info, setInfo] = useState("");
  const [available, setAvailable] = useState([]);
  const [busy, setBusy] = useState(false);
  const [synthCount, setSynthCount] = useState(0);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);

  async function refreshList() {
    try {
      const res = await api.listProfiles();
      setAvailable(res.profiles || []);
    } catch {
      setAvailable([]);
    }
  }

  useEffect(() => {
    refreshList();
  }, []);

  useEffect(() => {
    setPage(0); // revenir page 1 quand le filtre ou le registre change
  }, [query, available.length]);

  async function load(hash = userHash) {
    if (!hash) return;
    setLoading(true);
    setError("");
    setProfile(null);
    try {
      setProfile(await api.getProfile(hash));
      setUserHash(hash);
    } catch (e) {
      setError(e.message.includes("404") ? "Profil introuvable." : e.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadDemos() {
    setBusy(true);
    setError("");
    try {
      await api.seedDemo();
      await refreshList();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function generateMore() {
    setBusy(true);
    setError("");
    try {
      const n = synthCount + 12;
      const res = await api.seedSynthetic(n, 42);
      setSynthCount(n);
      setInfo(`${res.count} profils synthétiques générés (streamés en RAM).`);
      await refreshList();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function loadAmazonReal() {
    setBusy(true);
    setError("");
    setInfo("Construction de profils depuis les avis Amazon réels…");
    try {
      const res = await api.seedReviews("Subscription_Boxes", 800, 2);
      setInfo(
        `${res.count} profils RÉELS construits depuis les avis Amazon ` +
          `(${res.category}) — streamés en RAM.`
      );
      await refreshList();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
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
          `${res.interests.length} intérêts.`
      );
      await load(res.user_hash);
      await refreshList();
    } catch (e) {
      setError(e.message);
    } finally {
      setCrawling(false);
    }
  }

  const interests = profile?.interests || [];

  const q = query.trim().toLowerCase();
  const filtered = q
    ? available.filter(
        (p) =>
          (p.user_hash || "").toLowerCase().includes(q) ||
          (p.sector || "").toLowerCase().includes(q) ||
          (p.interests || []).some((i) => (i || "").toLowerCase().includes(q))
      )
    : available;

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageSafe = Math.min(page, pageCount - 1);
  const pageItems = filtered.slice(pageSafe * PAGE_SIZE, (pageSafe + 1) * PAGE_SIZE);

  return (
    <section>
      <h2>Profil utilisateur unifié</h2>
      <p className="section-lead">
        Fusion fédérée de signaux multi-plateformes en un profil unique. Les données
        brutes ne sont jamais persistées — seuls le hash SHA-256 et le profil dérivé
        subsistent.
      </p>

      {/* Profils disponibles — navigable */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="list-head">
          <h3 style={{ margin: 0 }}>
            <Icon name="database" size={15} /> Profils disponibles
            <span className="count-badge">
              {q ? `${filtered.length}/${available.length}` : available.length}
            </span>
          </h3>
          <div className="row" style={{ margin: 0, gap: 8 }}>
            <button className="btn secondary" onClick={loadDemos} disabled={busy}>
              {busy ? <Spinner /> : <Icon name="box" size={14} />} Profils démo
            </button>
            <button className="btn secondary" onClick={generateMore} disabled={busy}>
              {busy ? <Spinner /> : <Icon name="spark" size={14} />} + 12 synthétiques
            </button>
            <button
              className="btn"
              onClick={loadAmazonReal}
              disabled={busy}
              title="Construit de vrais profils depuis les avis Amazon (dataset McAuley)"
            >
              {busy ? <Spinner /> : <Icon name="box" size={14} />} Amazon réels
            </button>
          </div>
        </div>

        {available.length === 0 ? (
          <p className="muted" style={{ marginTop: 12 }}>
            Aucun profil dans le registre. Charge les profils démo ou génère des
            profils synthétiques.
          </p>
        ) : (
          <>
            <input
              className="input"
              placeholder="Filtrer par hash, secteur ou intérêt…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{ marginTop: 12 }}
            />
            {filtered.length === 0 ? (
              <p className="muted" style={{ marginTop: 12 }}>
                Aucun profil ne correspond à « {query} ».
              </p>
            ) : (
              <>
                <div className="profile-list">
                  {pageItems.map((p) => (
                    <button
                      key={p.user_hash}
                      className={`profile-item ${
                        userHash === p.user_hash ? "active" : ""
                      }`}
                      onClick={() => load(p.user_hash)}
                      title={p.user_hash}
                    >
                      <span className="pi-hash">{short(p.user_hash)}</span>
                      <span className="pi-meta">
                        {[p.sector, (p.interests || [])[0]]
                          .filter(Boolean)
                          .join(" · ")}
                      </span>
                    </button>
                  ))}
                </div>
                {pageCount > 1 && (
                  <div className="pager">
                    <button
                      className="btn secondary"
                      disabled={pageSafe === 0}
                      onClick={() => setPage(pageSafe - 1)}
                    >
                      <Icon name="refresh" size={13} /> Précédent
                    </button>
                    <span className="muted">
                      Page {pageSafe + 1} / {pageCount}
                    </span>
                    <button
                      className="btn secondary"
                      disabled={pageSafe >= pageCount - 1}
                      onClick={() => setPage(pageSafe + 1)}
                    >
                      Suivant
                    </button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>

      <div className="card tinted" style={{ marginBottom: 16 }}>
        <h3>
          <Icon name="search" size={15} /> Analyser un profil Reddit réel
        </h3>
        <p className="muted" style={{ marginTop: 0 }}>
          Crawl API Reddit → profil heuristique (subreddits + mots-clés). Nécessite
          les identifiants dans <code>.env</code>.
        </p>
        <div className="row" style={{ marginBottom: 0 }}>
          <input
            className="input"
            placeholder="pseudo Reddit (ex. spez)"
            value={redditUser}
            onChange={(e) => setRedditUser(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && crawlReddit()}
          />
          <button className="btn" onClick={crawlReddit} disabled={crawling}>
            {crawling ? <Spinner /> : <Icon name="search" size={15} />}
            {crawling ? "Analyse…" : "Analyser"}
          </button>
        </div>
      </div>

      <div className="row">
        <input
          className="input"
          placeholder="Hash utilisateur (SHA-256)"
          value={userHash}
          onChange={(e) => setUserHash(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <button className="btn secondary" onClick={() => load()} disabled={loading}>
          {loading ? <Spinner /> : <Icon name="refresh" size={15} />}
          {loading ? "Chargement…" : "Charger le profil"}
        </button>
      </div>

      {info && <Notice kind="ok">{info}</Notice>}
      {error && <Notice kind="error">{error}</Notice>}

      {!profile && !loading && !error && (
        <EmptyState
          icon="profile"
          title="Aucun profil chargé"
          children="Clique un profil ci-dessus, analyse un pseudo Reddit, ou saisis un hash."
        />
      )}

      {profile && (
        <div className="grid-3">
          <div className="card">
            <h3>Centres d'intérêt</h3>
            <RadarChart labels={interests.slice(0, 8)} />
            {interests.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <Chips items={interests.slice(0, 12)} />
              </div>
            )}
          </div>
          <div className="card">
            <h3>Profil professionnel</h3>
            {profile.professional && Object.keys(profile.professional).length ? (
              <pre className="json">
                {JSON.stringify(profile.professional, null, 2)}
              </pre>
            ) : (
              <p className="muted">Aucune donnée professionnelle.</p>
            )}
          </div>
          <div className="card">
            <h3>Consommation</h3>
            <Chips items={profile.consumption?.preferred_categories || []} />
            {!(profile.consumption?.preferred_categories || []).length && (
              <p className="muted">Aucune catégorie de consommation.</p>
            )}
            {profile.platforms_covered?.length > 0 && (
              <p className="muted" style={{ marginTop: 14 }}>
                Plateformes : {profile.platforms_covered.join(", ")}
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
