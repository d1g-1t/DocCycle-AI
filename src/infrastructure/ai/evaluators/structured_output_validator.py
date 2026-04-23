from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger(__name__)


@dataclass
class ValidationResult:

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    parsed: Any = None


class StructuredOutputValidator:

    @staticmethod
    def validate_json(raw: str) -> ValidationResult:
        """Parse raw string as JSON, attempt repair if needed."""
        # Try direct parse
        try:
            data = json.loads(raw)
            return ValidationResult(is_valid=True, parsed=data)
        except json.JSONDecodeError:
            pass

        cleaned = raw.strip()
        if "```json" in cleaned:
            start = cleaned.index("```json") + 7
            end = cleaned.index("```", start) if "```" in cleaned[start:] else len(cleaned)
            cleaned = cleaned[start:end].strip()
        elif "```" in cleaned:
            start = cleaned.index("```") + 3
            end = cleaned.index("```", start) if "```" in cleaned[start:] else len(cleaned)
            cleaned = cleaned[start:end].strip()

        try:
            data = json.loads(cleaned)
            log.debug("structured_output.repaired", method="code_block_extraction")
            return ValidationResult(is_valid=True, parsed=data)
        except json.JSONDecodeError:
            pass

        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start_idx = raw.find(start_char)
            end_idx = raw.rfind(end_char)
            if start_idx != -1 and end_idx > start_idx:
                candidate = raw[start_idx : end_idx + 1]
                try:
                    data = json.loads(candidate)
                    log.debug("structured_output.repaired", method="bracket_extraction")
                    return ValidationResult(is_valid=True, parsed=data)
                except json.JSONDecodeError:
                    continue

        return ValidationResult(
            is_valid=False,
            errors=[f"Cannot parse JSON from response: {raw[:200]}..."],
        )

    @staticmethod
    def validate_schema(
        data: Any,
        required_fields: list[str],
        field_types: dict[str, type] | None = None,
    ) -> ValidationResult:
        """Validate that parsed JSON has required fields and types."""
        errors: list[str] = []

        if not isinstance(data, dict):
            return ValidationResult(
                is_valid=False,
                errors=[f"Expected dict, got {type(data).__name__}"],
                parsed=data,
            )

        for field_name in required_fields:
            if field_name not in data:
                errors.append(f"Missing required field: {field_name}")

        if field_types:
            for field_name, expected_type in field_types.items():
                if field_name in data and not isinstance(data[field_name], expected_type):
                    errors.append(
                        f"Field '{field_name}' expected {expected_type.__name__}, "
                        f"got {type(data[field_name]).__name__}"
                    )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            parsed=data,
        )

    @classmethod
    def validate_clause_review(cls, raw: str) -> ValidationResult:
        """Validate a clause review response."""
        result = cls.validate_json(raw)
        if not result.is_valid:
            return result
        return cls.validate_schema(
            result.parsed,
            required_fields=["clause_type", "risk_level", "issues", "explanation"],
            field_types={"issues": list, "risk_level": str},
        )

    @classmethod
    def validate_obligation_extraction(cls, raw: str) -> ValidationResult:
        """Validate obligation extraction response (must be a list)."""
        result = cls.validate_json(raw)
        if not result.is_valid:
            return result
        if not isinstance(result.parsed, list):
            return ValidationResult(
                is_valid=False,
                errors=["Expected a JSON array of obligations"],
                parsed=result.parsed,
            )
        return result

    @classmethod
    def validate_risk_score(cls, raw: str) -> ValidationResult:
        """Validate risk score response."""
        result = cls.validate_json(raw)
        if not result.is_valid:
            return result
        schema_result = cls.validate_schema(
            result.parsed,
            required_fields=["risk_score", "summary"],
        )
        if schema_result.is_valid:
            score = schema_result.parsed.get("risk_score", 0)
            if not (0 <= score <= 100):
                schema_result.errors.append(
                    f"risk_score must be 0-100, got {score}"
                )
                schema_result.is_valid = False
        return schema_result
