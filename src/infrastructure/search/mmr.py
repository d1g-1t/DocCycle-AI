"""Maximal Marginal Relevance (MMR) re-ranking for diverse search results."""
from __future__ import annotations

import numpy as np


def mmr_rerank(
    query_embedding: list[float],
    candidate_embeddings: list[list[float]],
    candidate_scores: list[float],
    *,
    top_k: int = 10,
    lambda_param: float = 0.7,
) -> list[int]:
    """Return indices of top_k candidates selected via MMR.

    Args:
        query_embedding: Query vector.
        candidate_embeddings: List of candidate vectors.
        candidate_scores: Original relevance scores (0-1).
        top_k: Number of results to select.
        lambda_param: Balance relevance vs diversity (1.0=pure relevance).

    Returns:
        Ordered list of selected candidate indices.
    """
    if not candidate_embeddings:
        return []

    q = np.array(query_embedding)
    candidates = np.array(candidate_embeddings)
    scores = np.array(candidate_scores)

    selected: list[int] = []
    remaining = set(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = -1
        best_score = -float("inf")

        for idx in remaining:
            relevance = scores[idx]
            if selected:
                sim_to_selected = max(
                    _cosine_sim(candidates[idx], candidates[s]) for s in selected
                )
            else:
                sim_to_selected = 0.0

            mmr_score = lambda_param * relevance - (1 - lambda_param) * sim_to_selected
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx == -1:
            break
        selected.append(best_idx)
        remaining.discard(best_idx)

    return selected


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(dot / norm)
