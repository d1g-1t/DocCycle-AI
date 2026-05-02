"""Normalize extracted contract text for consistent processing."""
from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Clean and normalize contract text for downstream processing."""
    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Replace common special chars
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2014", "—").replace("\u2013", "–")

    # Collapse multiple whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove page breaks and form feeds
    text = text.replace("\f", "\n\n")

    # Strip leading/trailing whitespace on each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def normalize_clause_text(text: str) -> str:
    """Extra normalization for clause-level text."""
    text = normalize_text(text)
    # Remove leading numbering
    text = re.sub(r"^\d+\.\d*\s*", "", text)
    return text
