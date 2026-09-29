// Client API — appels vers l'API FastAPI (proxy Vite vers :8000 en dev).

async function request(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const detail = await resp.text().catch(() => "");
    throw new Error(`HTTP ${resp.status} — ${detail || resp.statusText}`);
  }
  return resp.json();
}

export const api = {
  health: () => request("/health"),

  getProfile: (userHash) =>
    request(`/api/v1/profile/${encodeURIComponent(userHash)}`),

  buildRedditProfile: (username, limit = 100) =>
    request("/api/v1/reddit/profile", {
      method: "POST",
      body: JSON.stringify({ username, limit }),
    }),

  recommendToUser: (userHash, catalog, topK) =>
    request("/api/v1/recommend/user", {
      method: "POST",
      body: JSON.stringify({ user_hash: userHash, catalog, top_k: topK }),
    }),

  recommendFromCatalog: (userHash, topK) =>
    request("/api/v1/recommend/catalog", {
      method: "POST",
      body: JSON.stringify({ user_hash: userHash, top_k: topK }),
    }),

  catalogInfo: () => request("/api/v1/catalog/info"),

  findCampaignTargets: (description, threshold) =>
    request("/api/v1/recommend/campaign", {
      method: "POST",
      body: JSON.stringify({ campaign: { description }, threshold }),
    }),

  listSegments: () => request("/api/v1/profiles/segments"),

  comparison: () => request("/api/v1/evaluate/comparison"),

  crawl: (payload) =>
    request("/api/v1/crawl", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
