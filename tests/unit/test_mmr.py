"""Unit tests for Maximal Marginal Relevance re-ranking."""
from __future__ import annotations

from src.infrastructure.search.mmr import mmr_rerank


def test_returns_top_k_results():
    q = [1.0, 0.0, 0.0]
    candidates = [[1.0, 0.0, 0.0], [0.9, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    scores = [0.95, 0.9, 0.3, 0.2]
    indices = mmr_rerank(q, candidates, scores, top_k=2)
    assert len(indices) == 2
    assert 0 in indices  # most relevant


def test_empty_candidates():
    indices = mmr_rerank([1.0], [], [], top_k=5)
    assert indices == []


def test_diversity_effect():
    q = [1.0, 0.0]
    candidates = [[1.0, 0.0], [0.99, 0.01], [0.0, 1.0]]
    scores = [0.95, 0.94, 0.5]
    # With high lambda (relevance-focused)
    high_lambda = mmr_rerank(q, candidates, scores, top_k=2, lambda_param=0.95)
    # With low lambda (diversity-focused)
    low_lambda = mmr_rerank(q, candidates, scores, top_k=2, lambda_param=0.3)
    # Low lambda should prefer more diverse results
    assert 2 in low_lambda  # diverse candidate likely selected
