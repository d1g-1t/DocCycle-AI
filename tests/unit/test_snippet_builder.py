"""Unit tests for search snippet builder."""
from __future__ import annotations

from src.infrastructure.search.snippet_builder import build_snippet


def test_highlights_query_terms():
    text = "The contract specifies unlimited liability for the vendor."
    snippet = build_snippet(text, "unlimited liability")
    assert "**unlimited**" in snippet or "**liability**" in snippet


def test_returns_text_without_match():
    text = "Short text here."
    snippet = build_snippet(text, "nonexistent")
    assert len(snippet) > 0


def test_truncates_long_text():
    text = "word " * 500
    snippet = build_snippet(text, "word", context_chars=100)
    assert len(snippet) < len(text)
