from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.playbook_rule import PlaybookRule


@dataclass
class PlaybookViolation:

    rule_id: str
    rule_name: str
    severity: str
    explanation: str
    fallback_clause_id: str | None


class PlaybookEvaluator:

    @staticmethod
    def evaluate(content_text: str, rules: list[PlaybookRule]) -> list[PlaybookViolation]:
        violations: list[PlaybookViolation] = []
        lower = content_text.lower()

        for rule in rules:
            if not rule.is_active:
                continue

            violated = False

            if rule.rule_type == "KEYWORD":
                keywords: list[str] = rule.condition_json.get("keywords", [])  # type: ignore[assignment]
                violated = all(kw.lower() in lower for kw in keywords)

            elif rule.rule_type == "CLAUSE_MISSING":
                required: list[str] = rule.condition_json.get("required_phrases", [])  # type: ignore[assignment]
                violated = not any(ph.lower() in lower for ph in required)

            elif rule.rule_type == "VALUE_THRESHOLD":
                pass

            if violated:
                violations.append(
                    PlaybookViolation(
                        rule_id=str(rule.id),
                        rule_name=rule.rule_name,
                        severity=rule.severity,
                        explanation=rule.explanation,
                        fallback_clause_id=str(rule.fallback_clause_id)
                        if rule.fallback_clause_id
                        else None,
                    )
                )

        return violations
