"""Génère le lot de figures de la thèse dans ``reports/figures/``.

Figures produites (PNG 300 dpi + PDF vectoriel pour LaTeX) :

1. ``fig_persona_clusters``   — séparation des profils par persona (RÉEL :
   Sentence-BERT + PCA, silhouette + Davies-Bouldin).
2. ``fig_reco_quality``       — Précision@K / NDCG@K du moteur content-based
   sur profils synthétiques (RÉEL : Sentence-BERT).
3. ``fig_architecture``       — diagramme des 5 couches + flux de données.
4. ``fig_protocol``           — protocole expérimental (holdout, configs A/B/C).
5. ``fig_exp_comparison``     — gabarit comparatif EXP-01 (valeurs d'EXEMPLE,
   à remplir avec les résultats d'entraînement réels).
6. ``fig_similarity_matrix``  — similarité inter-persona des profils (RÉEL).
7. ``fig_fragments_quality``  — séparabilité vs nombre de sources (RÉEL).
   ⚠ Observation : sur données synthétiques, une source (Reddit) sature déjà la
   métrique → NE valide PAS H2 (plateformes redondantes, pas complémentaires).
   La validation d'H2 requiert l'entraînement LoRA sur données réelles.

Palette Okabe-Ito (catégorielle daltonien-safe, ordre fixe).
Exécution : ``python scripts/make_figures.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

# Rendre le package `evaluation` (racine du dépôt) importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Okabe-Ito — palette catégorielle CVD-safe (ordre fixe, jamais cyclée).
PERSONA_COLORS: dict[str, str] = {
    "tech_ml": "#0072B2",
    "fitness_cycling": "#009E73",
    "foodie_cooking": "#E69F00",
    "finance_invest": "#CC79A7",
    "gamer_tech": "#D55E00",
    "eco_outdoor": "#56B4E9",
}
CONFIG_COLORS = {"fédéré": "#0072B2", "centralisé": "#E69F00", "mono-source": "#009E73"}
METRIC_COLORS = {"precision": "#0072B2", "ndcg": "#D55E00"}

# Catalogue de démonstration : 3 items par persona (pour la qualité de reco).
PERSONA_ITEMS: dict[str, list[tuple[str, str]]] = {
    "tech_ml": [
        ("GPU RTX 4070", "carte graphique deep learning"),
        ("livre machine learning", "apprentissage pytorch modèle"),
        ("clavier mécanique", "programmation code développeur"),
    ],
    "fitness_cycling": [
        ("vélo carbone", "cyclisme route endurance"),
        ("chaussures running", "course à pied marathon"),
        ("cardio-fréquencemètre", "entraînement sport fitness"),
    ],
    "foodie_cooking": [
        ("robot cuiseur", "cuisine recette plat"),
        ("couteau de chef", "cuisine découpe ingrédients"),
        ("poêle en fonte", "cuisson saveur repas"),
    ],
    "finance_invest": [
        ("livre finance", "investissement bourse portefeuille"),
        ("agenda premium", "budget planning gestion"),
        ("écran secondaire", "trading marché analyse"),
    ],
    "gamer_tech": [
        ("casque gaming", "jeu vidéo audio immersion"),
        ("carte graphique", "fps gaming performance"),
        ("chaise gaming", "confort jeu ergonomie"),
    ],
    "eco_outdoor": [
        ("gourde réutilisable", "zéro déchet durable"),
        ("sac de randonnée", "hiking nature plein air"),
        ("composteur", "jardin écologie recyclage"),
    ],
}

FIG_DIR = Path("reports/figures")


def _save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    print(f"[figure] {FIG_DIR}/{name}.png (+ .pdf)")


def _build_profiles(n_users: int, seed: int):
    """Construit n profils synthétiques + leur persona (label de vérité)."""
    from maha_these.core.anonymizer import DataAnonymizer
    from maha_these.data_generation.synthetic import SyntheticDataGenerator
    from maha_these.layer3_profile.heuristic_profile import HeuristicProfileBuilder

    gen = SyntheticDataGenerator(seed)
    anonymizer = DataAnonymizer()
    builder = HeuristicProfileBuilder()
    profiles, labels = [], []
    for i in range(n_users):
        username = f"user_{i}"
        data = anonymizer.anonymize(gen.generate_all(username))
        profiles.append(builder.build(data, data["user_hash"]))
        labels.append(gen.persona(username)["name"])
    return profiles, labels


# --------------------------------------------------------------------------- #
# 1. Séparation des profils par persona (RÉEL)
# --------------------------------------------------------------------------- #
def fig_persona_clusters(n_users: int = 60, seed: int = 42) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.metrics import davies_bouldin_score, silhouette_score

    from maha_these.layer4_recommendation.profile_encoder import ProfileEncoder

    profiles, labels = _build_profiles(n_users, seed)
    embeddings = np.asarray(ProfileEncoder().encode_profiles(profiles))
    xy = PCA(n_components=2, random_state=seed).fit_transform(embeddings)

    order = sorted(set(labels))
    label_ids = [order.index(label) for label in labels]
    silhouette = silhouette_score(embeddings, label_ids)
    davies_bouldin = davies_bouldin_score(embeddings, label_ids)

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    for name in order:
        idx = [j for j, label in enumerate(labels) if label == name]
        ax.scatter(
            xy[idx, 0],
            xy[idx, 1],
            s=64,
            c=PERSONA_COLORS.get(name, "#666666"),
            edgecolors="white",
            linewidths=0.8,
            label=name,
        )
    ax.set_xlabel("Composante principale 1")
    ax.set_ylabel("Composante principale 2")
    ax.set_title(
        "Séparation des profils par persona (Sentence-BERT + PCA)\n"
        f"silhouette = {silhouette:.2f}  ·  Davies-Bouldin = {davies_bouldin:.2f}"
        f"  ·  n = {n_users}"
    )
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, fontsize=9, title="Persona", loc="best")
    fig.tight_layout()
    _save(fig, "fig_persona_clusters")
    plt.close(fig)
    print(
        f"           silhouette={silhouette:.3f}  davies_bouldin={davies_bouldin:.3f}"
    )


# --------------------------------------------------------------------------- #
# 2. Qualité de recommandation (RÉEL)
# --------------------------------------------------------------------------- #
def fig_reco_quality(n_users: int = 48, seed: int = 42) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    from evaluation.metrics.profile_metrics import precision_at_k
    from evaluation.metrics.reco_metrics import ndcg_at_k
    from maha_these.layer4_recommendation.profile_encoder import ProfileEncoder

    profiles, labels = _build_profiles(n_users, seed)

    # catalogue étiqueté par persona (vérité terrain de pertinence)
    catalog = []
    for persona, items in PERSONA_ITEMS.items():
        for name, desc in items:
            catalog.append(
                {
                    "id": f"{persona}:{name}",
                    "text": f"{name} {desc}",
                    "persona": persona,
                }
            )

    encoder = ProfileEncoder()
    prof_emb = encoder.encode_profiles(profiles)
    cat_emb = encoder.encode([c["text"] for c in catalog])
    sims = cosine_similarity(prof_emb, cat_emb)  # (users, items)

    k_values = [3, 5, 10]
    prec = {k: [] for k in k_values}
    ndcg = {k: [] for k in k_values}
    for i, persona in enumerate(labels):
        ranking = [catalog[j]["id"] for j in np.argsort(sims[i])[::-1]]
        relevant = [c["id"] for c in catalog if c["persona"] == persona]
        for k in k_values:
            prec[k].append(precision_at_k(ranking, relevant, k))
            ndcg[k].append(ndcg_at_k(ranking, relevant, k))

    prec_mean = [float(np.mean(prec[k])) for k in k_values]
    ndcg_mean = [float(np.mean(ndcg[k])) for k in k_values]

    x = np.arange(len(k_values))
    w = 0.38
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    b1 = ax.bar(
        x - w / 2, prec_mean, w, color=METRIC_COLORS["precision"], label="Précision@K"
    )
    b2 = ax.bar(x + w / 2, ndcg_mean, w, color=METRIC_COLORS["ndcg"], label="NDCG@K")
    ax.bar_label(b1, fmt="%.2f", padding=3, fontsize=8)
    ax.bar_label(b2, fmt="%.2f", padding=3, fontsize=8)
    ax.set_xticks(x, [f"K={k}" for k in k_values])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score moyen")
    ax.set_title(
        "Qualité de recommandation content-based (Sentence-BERT)\n"
        f"catalogue étiqueté par persona · n = {n_users}"
    )
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    _save(fig, "fig_reco_quality")
    plt.close(fig)
    print(f"           P@5={prec_mean[1]:.3f}  NDCG@5={ndcg_mean[1]:.3f}")


# --------------------------------------------------------------------------- #
# Helper diagramme — boîte de texte
# --------------------------------------------------------------------------- #
def _box(ax, x, y, w, h, text, color, text_color="white", fontsize=10):
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=0,
            facecolor=color,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        color=text_color,
        fontsize=fontsize,
        wrap=True,
    )


def _arrow(ax, x, y0, y1, color="#555555"):
    ax.annotate(
        "",
        xy=(x, y1),
        xytext=(x, y0),
        arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.6},
    )


# --------------------------------------------------------------------------- #
# 3. Diagramme d'architecture (5 couches)
# --------------------------------------------------------------------------- #
def fig_architecture() -> None:
    import matplotlib.pyplot as plt

    layers = [
        (
            "Couche 1 — Crawling multi-plateformes\n(anonymisation SHA-256 → SessionBuffer RAM)",
            "#0072B2",
        ),
        (
            "Couche 2 — Fragmentation fédérée\n(préprocessing · LoRA local → Δθ)",
            "#009E73",
        ),
        (
            "Couche 3 — Agrégation fédérée (FedAvg)\n+ génération du profil global",
            "#E69F00",
        ),
        (
            "Couche 4 — Moteur de recommandation\n(Sentence-BERT · content-based · clustering)",
            "#CC79A7",
        ),
        ("Couche 5 — API REST (FastAPI) + Dashboard React", "#D55E00"),
    ]
    fig, ax = plt.subplots(figsize=(7.4, 7.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")

    w, h = 7.0, 1.5
    x = 1.5
    ys = [10, 8, 6, 4, 2]
    for (text, color), y in zip(layers, ys):
        _box(ax, x, y, w, h, text, color, fontsize=10)
    for y0, y1 in zip(ys[:-1], ys[1:]):
        _arrow(ax, x + w / 2, y0, y1 + h)

    # annotation confidentialité
    ax.text(
        x + w / 2,
        11.9,
        "Principe : « ne pas enregistrer les data » — RAM only · seuls les Δθ "
        "et le profil anonymisé sortent",
        ha="center",
        va="center",
        fontsize=9,
        style="italic",
        color="#333333",
    )
    ax.set_title("Architecture du système fédéré de profilage", fontsize=12, pad=6)
    fig.tight_layout()
    _save(fig, "fig_architecture")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 4. Protocole expérimental
# --------------------------------------------------------------------------- #
def fig_protocol() -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8.0, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    _box(
        ax,
        4,
        8.4,
        4,
        1.1,
        "Données\n(holdout 80 / 20 · seed = 42)",
        "#555555",
        fontsize=10,
    )

    configs = [
        (0.6, "Config A — FÉDÉRÉ\n(Trainer×N + FedAvg)\n← proposé", "#0072B2"),
        (
            4.4,
            "Config B — CENTRALISÉ\n(données fusionnées)\n← baseline haute",
            "#E69F00",
        ),
        (8.2, "Config C — MONO-SOURCE\n(1 plateforme)\n← baseline basse", "#009E73"),
    ]
    for cx, text, color in configs:
        _box(ax, cx, 5.4, 3.2, 1.9, text, color, fontsize=9)
        _arrow(ax, cx + 1.6, 8.4, 5.4 + 1.9)

    _box(
        ax,
        1.0,
        3.0,
        10.0,
        1.4,
        "Métriques : Précision@K · NDCG@K · cohérence-BERT\nROUGE-L · Davies-Bouldin",
        "#CC79A7",
        fontsize=10,
    )
    for cx, _, _ in configs:
        _arrow(ax, cx + 1.6, 5.4, 3.0 + 1.4)

    _box(
        ax,
        2.5,
        0.6,
        7.0,
        1.4,
        "Comparaison A vs B vs C\ntest de Wilcoxon (validation H1)",
        "#D55E00",
        fontsize=10,
    )
    _arrow(ax, 6.0, 3.0, 0.6 + 1.4)

    ax.set_title("Protocole expérimental (EXP-01)", fontsize=12, pad=6)
    fig.tight_layout()
    _save(fig, "fig_protocol")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 5. Gabarit comparatif EXP-01 (valeurs d'EXEMPLE)
# --------------------------------------------------------------------------- #
def fig_exp_comparison() -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    metrics = ["Précision@5", "NDCG@10", "Cohérence-BERT"]
    # ⚠️ Valeurs d'EXEMPLE (structure) — à remplacer par les résultats réels.
    example = {
        "fédéré": [0.71, 0.68, 0.82],
        "centralisé": [0.74, 0.70, 0.84],
        "mono-source": [0.55, 0.52, 0.69],
    }
    x = np.arange(len(metrics))
    w = 0.26
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    for i, (config, vals) in enumerate(example.items()):
        ax.bar(x + (i - 1) * w, vals, w, color=CONFIG_COLORS[config], label=config)
    ax.set_xticks(x, metrics)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score")
    ax.set_title(
        "Comparaison fédéré vs centralisé vs mono-source (EXP-01)\n"
        "⚠ valeurs d'EXEMPLE — gabarit à remplir avec les résultats d'entraînement"
    )
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(
        frameon=False,
        fontsize=9,
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
    )
    fig.tight_layout()
    _save(fig, "fig_exp_comparison")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 6. Matrice de similarité inter-persona (RÉEL)
# --------------------------------------------------------------------------- #
def fig_similarity_matrix(n_users: int = 60, seed: int = 42) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    from maha_these.layer4_recommendation.profile_encoder import ProfileEncoder

    profiles, labels = _build_profiles(n_users, seed)
    emb = np.asarray(ProfileEncoder().encode_profiles(profiles))

    personas = sorted(set(labels))
    centroids = np.array(
        [
            emb[[i for i, lbl in enumerate(labels) if lbl == p]].mean(axis=0)
            for p in personas
        ]
    )
    sim = cosine_similarity(centroids)

    fig, ax = plt.subplots(figsize=(6.8, 5.8))
    im = ax.imshow(sim, cmap="Blues", vmin=0, vmax=1)  # séquentiel = magnitude
    ax.set_xticks(range(len(personas)), personas, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(personas)), personas, fontsize=9)
    for i in range(len(personas)):
        for j in range(len(personas)):
            ax.text(
                j,
                i,
                f"{sim[i, j]:.2f}",
                ha="center",
                va="center",
                color="white" if sim[i, j] > 0.6 else "#222222",
                fontsize=8,
            )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Similarité cosinus")
    ax.set_title("Similarité inter-persona des profils (Sentence-BERT)")
    fig.tight_layout()
    _save(fig, "fig_similarity_matrix")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 7. Séparabilité des profils vs nombre de sources (RÉEL, profils heuristiques)
#    Observation honnête : saturation dès 1 source sur données synthétiques.
# --------------------------------------------------------------------------- #
def fig_fragments_quality(n_users: int = 48, seed: int = 42) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.metrics import silhouette_score

    from maha_these.core.anonymizer import DataAnonymizer
    from maha_these.data_generation.synthetic import SyntheticDataGenerator
    from maha_these.layer3_profile.heuristic_profile import HeuristicProfileBuilder
    from maha_these.layer4_recommendation.profile_encoder import ProfileEncoder

    gen = SyntheticDataGenerator(seed)
    anonymizer = DataAnonymizer()
    builder = HeuristicProfileBuilder()
    encoder = ProfileEncoder()

    platform_sets = {
        1: ["reddit"],
        2: ["reddit", "amazon"],
        3: ["reddit", "amazon", "linkedin"],
    }
    generators = {
        "reddit": gen.generate_reddit,
        "amazon": gen.generate_amazon,
        "linkedin": gen.generate_linkedin,
    }
    score_by_n = {}
    for n, plats in platform_sets.items():
        profiles, labels = [], []
        for i in range(n_users):
            username = f"user_{i}"
            raw = {"username": username}
            for platform in plats:
                raw.update(
                    {
                        k: v
                        for k, v in generators[platform](username).items()
                        if k != "username"
                    }
                )
            data = anonymizer.anonymize(raw)
            profiles.append(builder.build(data, data["user_hash"]))
            labels.append(gen.persona(username)["name"])
        emb = np.asarray(encoder.encode_profiles(profiles))
        order = sorted(set(labels))
        ids = [order.index(label) for label in labels]
        score_by_n[n] = float(silhouette_score(emb, ids))

    xs = list(platform_sets)
    ys = [score_by_n[n] for n in xs]
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot(
        xs,
        ys,
        marker="o",
        color="#0072B2",
        linewidth=2,
        markersize=10,
        markeredgecolor="white",
    )
    for x, y in zip(xs, ys):
        ax.annotate(
            f"{y:.3f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
        )
    ax.set_xticks(xs)
    ax.set_xlabel("Nombre de plateformes fédérées")
    ax.set_ylabel("Silhouette (séparabilité des personas)")
    ax.set_ylim(min(ys) - 0.08, 1.0)
    ax.set_title(
        "Séparabilité des profils vs nombre de sources fédérées\n"
        f"profils heuristiques · n = {n_users}"
    )
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    _save(fig, "fig_fragments_quality")
    plt.close(fig)
    print(f"           silhouette par nb de sources : {score_by_n}")


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "figure.dpi": 120})

    fig_persona_clusters()
    fig_reco_quality()
    fig_architecture()
    fig_protocol()
    fig_exp_comparison()
    fig_similarity_matrix()
    fig_fragments_quality()
    print(f"\n{7} figures générées dans {FIG_DIR}/ (PNG + PDF).")


if __name__ == "__main__":
    main()
