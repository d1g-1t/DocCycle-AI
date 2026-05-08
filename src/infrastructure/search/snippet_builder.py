"""Build highlighted search snippets from matched chunks."""
from __future__ import annotations

import re


def build_snippet(text: str, query: str, *, context_chars: int = 150) -> str:
    """Extract a snippet from text around the best match for query terms."""
    words = query.lower().split()
    best_pos = 0
    best_score = 0
    lower_text = text.lower()

    for i in range(0, len(text) - 10, 20):
        window = lower_text[i : i + context_chars * 2]
        score = sum(1 for w in words if w in window)
        if score > best_score:
            best_score = score
            best_pos = i

    start = max(0, best_pos - context_chars // 2)
    end = min(len(text), best_pos + context_chars * 2)
    snippet = text[start:end].strip()

    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"

    # Highlight matched terms
    for word in words:
        if len(word) >= 3:
            snippet = re.sub(
                rf"({re.escape(word)})",
                r"**\1**",
                snippet,
                flags=re.IGNORECASE,
            )

    return snippet
