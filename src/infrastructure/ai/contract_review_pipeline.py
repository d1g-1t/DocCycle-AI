from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field

import structlog

from src.application.interfaces.i_llm_service import ILlmService, LlmMessage

log = structlog.get_logger(__name__)

REVIEW_SYSTEM_PROMPT = """You are a senior legal AI assistant specialized in contract review.
You analyze contract clauses and identify risks, non-standard language, and playbook deviations.
Always respond with valid JSON matching the requested schema. Be precise and concise."""

CLAUSE_REVIEW_PROMPT_TEMPLATE = """Analyze the following contract clause and return JSON with this schema:
{{
  "clause_type": "<type of clause>",
  "risk_level": "low|medium|high|critical",
  "issues": ["<issue 1>", ...],
  "suggested_redline": "<improved language or null if no change needed>",
  "explanation": "<brief explanation>"
}}

--- CLAUSE ---
{clause_text}
--- END ---"""

RISK_SCORE_PROMPT = """Given the following list of clause review results from a contract review,
calculate an overall risk score (0-100, where 0=no risk, 100=extreme risk).
Return JSON: {{"risk_score": <number>, "summary": "<2-3 sentence summary>"}}

Clause reviews:
{reviews_json}"""


@dataclass
class ClauseReviewResult:
    clause_text: str
    clause_type: str
    risk_level: str
    issues: list[str]
    suggested_redline: str | None
    explanation: str


@dataclass
class ReviewPipelineResult:
    run_id: uuid.UUID
    contract_id: uuid.UUID
    risk_score: int
    summary: str
    clause_reviews: list[ClauseReviewResult] = field(default_factory=list)
    playbook_deviations: list[str] = field(default_factory=list)


class ContractReviewPipeline:

    def __init__(self, llm: ILlmService) -> None:
        self._llm = llm

    async def run(
        self,
        run_id: uuid.UUID,
        contract_id: uuid.UUID,
        contract_html: str,
        clauses: list[str],
        playbook_rules: list[str] | None = None,
    ) -> ReviewPipelineResult:
        log.info("review_pipeline.start", run_id=str(run_id), clauses=len(clauses))

        clause_results: list[ClauseReviewResult] = []
        for clause in clauses:
            result = await self._review_clause(clause)
            clause_results.append(result)

        risk_result = await self._score_risk(clause_results)

        playbook_deviations: list[str] = []
        if playbook_rules:
            playbook_deviations = await self._check_playbook(contract_html, playbook_rules)

        log.info(
            "review_pipeline.complete",
            run_id=str(run_id),
            risk_score=risk_result["risk_score"],
        )
        return ReviewPipelineResult(
            run_id=run_id,
            contract_id=contract_id,
            risk_score=int(risk_result["risk_score"]),
            summary=risk_result["summary"],
            clause_reviews=clause_results,
            playbook_deviations=playbook_deviations,
        )

    async def _review_clause(self, clause_text: str) -> ClauseReviewResult:
        prompt = CLAUSE_REVIEW_PROMPT_TEMPLATE.format(clause_text=clause_text[:3000])
        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content=REVIEW_SYSTEM_PROMPT),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.1,
        )
        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            data = {
                "clause_type": "unknown",
                "risk_level": "medium",
                "issues": ["Failed to parse AI response"],
                "suggested_redline": None,
                "explanation": resp.content[:500],
            }
        return ClauseReviewResult(
            clause_text=clause_text,
            clause_type=data.get("clause_type", "unknown"),
            risk_level=data.get("risk_level", "medium"),
            issues=data.get("issues", []),
            suggested_redline=data.get("suggested_redline"),
            explanation=data.get("explanation", ""),
        )

    async def _score_risk(self, reviews: list[ClauseReviewResult]) -> dict:
        reviews_json = json.dumps(
            [
                {
                    "clause_type": r.clause_type,
                    "risk_level": r.risk_level,
                    "issues": r.issues,
                }
                for r in reviews
            ],
            ensure_ascii=False,
        )
        prompt = RISK_SCORE_PROMPT.format(reviews_json=reviews_json[:6000])
        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content=REVIEW_SYSTEM_PROMPT),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.1,
        )
        try:
            return json.loads(resp.content)
        except json.JSONDecodeError:
            return {"risk_score": 50, "summary": "Could not parse risk assessment."}

    async def _check_playbook(self, contract_html: str, rules: list[str]) -> list[str]:
        rules_text = "\n".join(f"- {r}" for r in rules[:20])
        prompt = f"""Check if the following contract violates any of these playbook rules.
Return JSON: {{"violations": ["<violated rule 1>", ...]}}

RULES:
{rules_text}

CONTRACT (excerpt):
{contract_html[:4000]}"""
        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content=REVIEW_SYSTEM_PROMPT),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.1,
        )
        try:
            return json.loads(resp.content).get("violations", [])
        except json.JSONDecodeError:
            return []
