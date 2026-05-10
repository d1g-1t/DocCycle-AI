"""Unit tests for the clause splitter."""
from __future__ import annotations

import pytest

from src.infrastructure.parsing.clause_splitter import extract_text_from_html, split_into_clauses


def test_split_by_section_headings() -> None:
    text = """SECTION 1. Definitions
The terms used herein shall have the meanings set forth below.
"Agreement" means this contract.

SECTION 2. Payment
All payments shall be made within 30 days of invoice.
Late payments accrue interest at 1.5% per month.

SECTION 3. Termination
Either party may terminate this Agreement with 30 days written notice."""
    clauses = split_into_clauses(text)
    assert len(clauses) >= 2
    assert all(len(c) >= 10 for c in clauses)


def test_split_by_paragraphs_fallback() -> None:
    text = "First paragraph with some content here.\n\nSecond paragraph with other content here.\n\nThird paragraph."
    clauses = split_into_clauses(text)
    assert len(clauses) >= 1


def test_empty_text_returns_something() -> None:
    clauses = split_into_clauses("")
    assert len(clauses) == 0 or clauses == [""]


def test_long_clause_is_broken() -> None:
    long_clause = "This is a sentence. " * 200  # very long
    clauses = split_into_clauses(long_clause, max_length=500)
    assert all(len(c) <= 600 for c in clauses)  # a bit of slack around sentence boundaries


def test_extract_text_from_html_strips_tags() -> None:
    html = "<h1>Title</h1><p>Some <b>bold</b> text &nbsp; here.</p>"
    text = extract_text_from_html(html)
    assert "<" not in text
    assert "bold" in text
    assert "Title" in text
