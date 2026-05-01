"""Centralized prompt templates for AI contract review."""
from __future__ import annotations

SYSTEM_PROMPT = """You are a senior legal AI assistant for ContractForge CLM platform.
You specialize in Russian and international commercial contracts.
Always respond with valid JSON matching the requested schema.
Be precise, concise, and cite specific clauses when possible."""

CLAUSE_ANALYSIS_PROMPT = """Analyze this contract clause and return JSON:
{{
  "clause_type": "<type>",
  "risk_level": "low|medium|high|critical",
  "issues": ["<issue>"],
  "suggested_redline": "<improved text or null>",
  "explanation": "<brief explanation>",
  "category": "<LIABILITY|INDEMNIFICATION|TERMINATION|CONFIDENTIALITY|IP_OWNERSHIP|FORCE_MAJEURE|GOVERNING_LAW|DISPUTE_RESOLUTION|PAYMENT_TERMS|WARRANTY|OTHER>"
}}

CLAUSE:
{clause_text}"""

RISK_ASSESSMENT_PROMPT = """Given these clause review results, compute an overall risk score.
Return JSON: {{"risk_score": <0-100>, "summary": "<2-3 sentences>", "red_flags": ["<flag>"]}}

Reviews:
{reviews_json}"""

OBLIGATION_EXTRACTION_PROMPT = """Extract all obligations from this contract text.
Return JSON array:
[{{"title": "<title>", "description": "<details>", "responsible_role": "CONTRACTOR|CLIENT|BOTH|null",
   "due_date": "<ISO 8601 or null>", "penalty_text": "<text or null>",
   "renewal_window_start": "<ISO 8601 or null>", "renewal_window_end": "<ISO 8601 or null>"}}]

CONTRACT:
{text}"""

NEGOTIATION_SUMMARY_PROMPT = """Compare these two contract versions and generate a negotiation summary.
Return JSON:
{{"changes": [{{"section": "<section>", "change_type": "added|removed|modified",
   "original": "<text>", "revised": "<text>", "impact": "<explanation>"}}],
 "summary": "<overall summary>"}}

ORIGINAL:
{original_text}

REVISED:
{revised_text}"""
