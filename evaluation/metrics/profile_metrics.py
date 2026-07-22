"""Métriques orientées profil : Précision@K, cohérence sémantique, ROUGE-L."""

from __future__ import annotations

from typing import Any, Sequence


def precision_at_k(predicted: Sequence[Any], relevant: Sequence[Any], k: int) -> float:
    """Proportion d'items pertinents parmi les K premières prédictions."""
    if k <= 0:
        return 0.0
    top_k = list(predicted)[:k]
    if not top_k:
        return 0.0
    relevant_set = set(relevant)
    hits = sum(1 for item in top_k if item in relevant_set)
    return hits / len(top_k)


def semantic_coherence(profile_text: str, source_texts: Sequence[str]) -> float:
    """Cosinus moyen entre l'embedding du profil et celui des sources.

    Mesure à quel point le profil généré reste fidèle aux données sources.
    """
    from sentence_transformers import SentenceTransformer, util  # import paresseux

    model = SentenceTransformer("all-mpnet-base-v2")
    prof_emb = model.encode(profile_text, convert_to_tensor=True)
    src_emb = model.encode(list(source_texts), convert_to_tensor=True)
    sims = util.cos_sim(prof_emb, src_emb)
    return float(sims.mean())


def rouge_l(profile_text: str, reference_text: str) -> float:
    """Score ROUGE-L (F-mesure) entre profil généré et référence."""
    from rouge_score import rouge_scorer  # import paresseux

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    return scorer.score(reference_text, profile_text)["rougeL"].fmeasure
