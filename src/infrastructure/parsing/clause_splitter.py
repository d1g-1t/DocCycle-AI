"""Rule-based clause splitter for contract text."""
from __future__ import annotations

import re

# Typical clause delimiters in legal drafting
_HEADING_PATTERN = re.compile(
    r"(?:^|\n)(?:ARTICLE|SECTION|CLAUSE|§|\d+\.)\s+.{3,80}",
    re.IGNORECASE | re.MULTILINE,
)
_MIN_CLAUSE_LEN = 100  # chars — shorter splits are noise


def split_into_clauses(text: str, max_length: int = 2000) -> list[str]:
    """Split contract text into meaningful clause chunks.

    Strategy:
    1. Try to split on recognizable legal headings.
    2. Fall back to paragraph splitting.
    3. Merge tiny fragments with the next chunk.
    4. Break oversized chunks at sentence boundaries.
    """
    # Step 1 — split on headings
    splits = _HEADING_PATTERN.split(text)
    # Headings themselves become part of subsequent clause via re.split with groups
    chunks = [s.strip() for s in splits if s and s.strip()]

    # Step 2 — if no headings found, split by double-newline (paragraphs)
    if len(chunks) <= 1:
        chunks = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    # Step 3 — merge tiny fragments
    merged: list[str] = []
    buf = ""
    for chunk in chunks:
        if len(buf) + len(chunk) < _MIN_CLAUSE_LEN:
            buf += " " + chunk
        else:
            if buf:
                merged.append(buf.strip())
            buf = chunk
    if buf:
        merged.append(buf.strip())

    # Step 4 — break oversized chunks
    result: list[str] = []
    for chunk in merged:
        if len(chunk) <= max_length:
            result.append(chunk)
        else:
            result.extend(_break_on_sentences(chunk, max_length))

    return result or [text[:max_length]]


def _break_on_sentences(text: str, max_length: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts: list[str] = []
    buf = ""
    for s in sentences:
        if len(buf) + len(s) <= max_length:
            buf += (" " if buf else "") + s
        else:
            if buf:
                parts.append(buf)
            buf = s
    if buf:
        parts.append(buf)
    return parts


def extract_text_from_html(html: str) -> str:
    """Strip HTML tags for plain-text clause splitting."""
    import re as _re
    text = _re.sub(r"<[^>]+>", " ", html)
    text = _re.sub(r"&nbsp;", " ", text)
    text = _re.sub(r"\s{2,}", " ", text)
    return text.strip()
