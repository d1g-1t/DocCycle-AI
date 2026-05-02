"""Semantic contract chunker — splits text into meaningful sections."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ContractChunk:
    """A chunk of contract text with metadata."""
    index: int
    text: str
    section_title: str | None = None
    char_offset: int = 0


_SECTION_RE = re.compile(
    r"(?:^|\n\n)(?:(?:ARTICLE|SECTION|CLAUSE|PART|APPENDIX|EXHIBIT|SCHEDULE|ANNEX)\s+\S+[.:\s]|"
    r"\d+\.\d*\s+[A-ZА-Я])",
    re.MULTILINE,
)


def chunk_contract(text: str, max_chunk_size: int = 1500, overlap: int = 200) -> list[ContractChunk]:
    """Split a contract into overlapping semantic chunks."""
    sections = _split_by_sections(text)
    chunks: list[ContractChunk] = []
    idx = 0

    for title, body in sections:
        if len(body) <= max_chunk_size:
            chunks.append(ContractChunk(index=idx, text=body.strip(), section_title=title))
            idx += 1
        else:
            sub_chunks = _sliding_window(body, max_chunk_size, overlap)
            for sc in sub_chunks:
                chunks.append(ContractChunk(index=idx, text=sc.strip(), section_title=title))
                idx += 1

    return chunks or [ContractChunk(index=0, text=text[:max_chunk_size])]


def _split_by_sections(text: str) -> list[tuple[str | None, str]]:
    """Split by section headings."""
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return [(None, text)]

    sections: list[tuple[str | None, str]] = []
    if matches[0].start() > 0:
        sections.append((None, text[: matches[0].start()]))

    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group().strip()
        body = text[m.end() : end]
        sections.append((title, body))

    return sections


def _sliding_window(text: str, size: int, overlap: int) -> list[str]:
    """Create overlapping chunks via sliding window."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks
