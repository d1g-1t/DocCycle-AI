"""Prompt loader — loads and caches prompt templates from .md files."""
from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Map logical prompt names to .md file names
_PROMPT_FILES: dict[str, str] = {
    "system": "",  # system prompt is inline — no separate file
    "clause_classifier": "clause_classifier_prompt.md",
    "clause_analysis": "contract_review_prompt.md",
    "contract_review": "contract_review_prompt.md",
    "clause_suggestion": "clause_suggestion_prompt.md",
    "negotiation_summary": "negotiation_summary_prompt.md",
    "obligation_extraction": "obligation_extraction_prompt.md",
    "review_verifier": "review_verifier_prompt.md",
    "risk_assessment": "",  # inline fallback
}

_SYSTEM_PROMPT = """You are a senior legal AI assistant for ContractForge CLM platform.
You specialize in Russian and international commercial contracts.
Always respond with valid JSON matching the requested schema.
Be precise, concise, and cite specific clauses when possible."""

_RISK_ASSESSMENT_FALLBACK = """Given these clause review results, compute an overall risk score.
Return JSON: {{"risk_score": <0-100>, "summary": "<2-3 sentences>", "red_flags": ["<flag>"]}}

Reviews:
{reviews_json}"""


@lru_cache(maxsize=32)
def get_prompt(name: str) -> str:
    """Get a prompt template by name. Loads from .md file or falls back to inline."""
    if name == "system":
        return _SYSTEM_PROMPT
    if name == "risk_assessment":
        return _RISK_ASSESSMENT_FALLBACK

    filename = _PROMPT_FILES.get(name)
    if not filename:
        raise KeyError(f"Unknown prompt template: {name}")

    path = _PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")

    raise KeyError(f"Prompt file not found: {path}")


def render_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template and substitute variables."""
    template = get_prompt(name)
    return template.format(**kwargs)


def prompt_hash(name: str) -> str:
    """Return SHA-256 hash of a prompt template for audit logging."""
    template = get_prompt(name)
    return hashlib.sha256(template.encode()).hexdigest()[:16]
