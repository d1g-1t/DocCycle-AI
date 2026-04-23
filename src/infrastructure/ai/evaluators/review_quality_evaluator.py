from __future__ import annotations

from dataclasses import dataclass, field

from src.infrastructure.ai.contract_review_pipeline import ClauseReviewResult, ReviewPipelineResult


@dataclass
class QualityScore:
    overall: float = 0.0  # 0-1
    completeness: float = 0.0
    consistency: float = 0.0
    specificity: float = 0.0
    issues: list[str] = field(default_factory=list)


class ReviewQualityEvaluator:

    @staticmethod
    def evaluate(result: ReviewPipelineResult) -> QualityScore:
        """Score the quality of a review pipeline output."""
        score = QualityScore()
        issues: list[str] = []

        if not result.clause_reviews:
            issues.append("No clause reviews produced")
            score.completeness = 0.0
        else:
            score.completeness = min(1.0, len(result.clause_reviews) / 5)

        if result.risk_score < 0 or result.risk_score > 100:
            issues.append(f"Risk score out of range: {result.risk_score}")

        high_risk_clauses = sum(
            1 for c in result.clause_reviews if c.risk_level in ("high", "critical")
        )
        if high_risk_clauses > 0 and result.risk_score < 30:
            issues.append("High-risk clauses found but overall score is low")
            score.consistency = 0.3
        elif high_risk_clauses == 0 and result.risk_score > 70:
            issues.append("No high-risk clauses but overall score is very high")
            score.consistency = 0.3
        else:
            score.consistency = 1.0

        reviews_with_issues = sum(1 for c in result.clause_reviews if c.issues)
        if result.clause_reviews:
            score.specificity = reviews_with_issues / len(result.clause_reviews)
        else:
            score.specificity = 0.0

        score.issues = issues
        score.overall = (score.completeness + score.consistency + score.specificity) / 3
        return score
