"""Unit tests for contract chunker."""
from __future__ import annotations

from src.infrastructure.parsing.contract_chunker import chunk_contract, ContractChunk


def test_short_text_single_chunk():
    text = "This is a short contract."
    chunks = chunk_contract(text)
    assert len(chunks) == 1
    assert chunks[0].text == text


def test_long_text_multiple_chunks():
    text = "A" * 5000
    chunks = chunk_contract(text, max_chunk_size=1000, overlap=100)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.text) <= 1100  # some slack


def test_sections_produce_separate_chunks():
    text = """ARTICLE 1. Definitions
Terms defined here.

ARTICLE 2. Payment
All payments shall be made in USD.

ARTICLE 3. Termination
Either party may terminate."""
    chunks = chunk_contract(text)
    assert len(chunks) >= 2


def test_chunk_has_index():
    text = "Some text.\n\nMore text.\n\nFinal text."
    chunks = chunk_contract(text)
    for i, chunk in enumerate(chunks):
        assert chunk.index == i
