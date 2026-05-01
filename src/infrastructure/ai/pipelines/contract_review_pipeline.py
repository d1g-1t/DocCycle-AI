"""AI pipeline for full contract review — wraps clause analysis + risk scoring."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field

import structlog

from src.application.interfaces.i_llm_service import ILlmService, LlmMessage
from src.infrastructure.ai.services.prompt_loader import get_prompt, render_prompt

log = structlog.get_logger(__name__)


@dataclass
class ClauseReviewResult:
    """Review result for a single clause."""

    clause_text: str
    clause_type: str
    risk_level: str
    issues: list[str]
    suggested_redline: str | None
    explanation: str
    category: str = "OTHER"


@dataclass
class ReviewPipelineResult:
    """Full contract review output."""

    run_id: uuid.UUID
    contract_id: uuid.UUID
    risk_score: int
    summary: str
    red_flags: list[str] = field(default_factory=list)
    clause_reviews: list[ClauseReviewResult] = field(default_factory=list)
    playbook_deviations: list[str] = field(default_factory=list)


class ContractReviewPipeline:
    """Orchestrates multi-step AI review of a contract."""

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
        """Run full review: clause-by-clause analysis → risk score → playbook check."""
        log.info("review_pipeline.start", run_id=str(run_id), clauses=len(clauses))

        system = get_prompt("system")
        review_prompt_tpl = get_prompt("contract_review")

        # Step 1: review each clause
        clause_results: list[ClauseReviewResult] = []
        for clause in clauses:
            result = await self._review_clause(clause, system, review_prompt_tpl)
            clause_results.append(result)

        # Step 2: compute overall risk score
        risk_result = await self._score_risk(clause_results, system)

        # Step 3: playbook deviation check
        playbook_deviations: list[str] = []
        if playbook_rules:
            playbook_deviations = await self._check_playbook(
                contract_html, playbook_rules, system
            )

        log.info(
            "review_pipeline.complete",
            run_id=str(run_id),
            risk_score=risk_result.get("risk_score", 50),
        )
        return ReviewPipelineResult(
            run_id=run_id,
            contract_id=contract_id,
            risk_score=int(risk_result.get("risk_score", 50)),
            summary=risk_result.get("summary", ""),
            red_flags=risk_result.get("red_flags", []),
            clause_reviews=clause_results,
            playbook_deviations=playbook_deviations,
        )

    async def _review_clause(
        self, clause_text: str, system: str, prompt_tpl: str
    ) -> ClauseReviewResult:
        prompt = prompt_tpl.replace("{clause_text}", clause_text[:3000])
        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content=system),
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
            category=data.get("category", "OTHER"),
        )

    async def _score_risk(
        self, reviews: list[ClauseReviewResult], system: str
    ) -> dict:
        reviews_json = json.dumps(
            [
                {
                    "clause_type": r.clause_type,
                    "risk_level": r.risk_level,
                    "issues": r.issues,
                    "category": r.category,
                }
                for r in reviews
            ],
            ensure_ascii=False,
        )
        prompt = render_prompt("risk_assessment", reviews_json=reviews_json[:6000])
        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content=system),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.1,
        )
        try:
            return json.loads(resp.content)
        except json.JSONDecodeError:
            return {"risk_score": 50, "summary": "Could not parse risk assessment."}

    async def _check_playbook(
        self, contract_html: str, rules: list[str], system: str
    ) -> list[str]:
        rules_text = "\n".join(f"- {r}" for r in rules[:20])
        prompt = (
            f"Check if the following contract violates any of these playbook rules.\n"
            f'Return JSON: {{"violations": ["<violated rule 1>", ...]}}\n\n'
            f"RULES:\n{rules_text}\n\n"
            f"CONTRACT (excerpt):\n{contract_html[:4000]}"
        )
        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content=system),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.1,
        )
        try:
            return json.loads(resp.content).get("violations", [])
        except json.JSONDecodeError:
            return []
