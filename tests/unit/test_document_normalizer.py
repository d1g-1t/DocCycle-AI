"""Unit tests for document normalizer."""
from __future__ import annotations

from src.infrastructure.parsing.document_normalizer import normalize_text, normalize_clause_text


def test_collapse_whitespace():
    text = "Hello    world   from   contract"
    assert "    " not in normalize_text(text)
    assert "Hello world from contract" == normalize_text(text)


def test_normalize_unicode_quotes():
    text = "\u201cHello\u201d and \u2018world\u2019"
    result = normalize_text(text)
    assert '"Hello"' in result
    assert "'world'" in result


def test_collapse_multiple_newlines():
    text = "Line1\n\n\n\n\nLine2"
    result = normalize_text(text)
    assert "\n\n\n" not in result
    assert "Line1" in result and "Line2" in result


def test_normalize_clause_strips_numbering():
    text = "3.1 The following terms apply"
    result = normalize_clause_text(text)
    assert result.startswith("The following")
