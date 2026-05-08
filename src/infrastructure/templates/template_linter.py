"""Template linter — checks quality and best practices of template DSL."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.infrastructure.templates.dsl_models import TemplateDSL


@dataclass
class LintResult:
    score: int = 100
    suggestions: list[str] = field(default_factory=list)


def lint_template(dsl: TemplateDSL) -> LintResult:
    """Lint a template DSL for best practices. Returns score 0-100."""
    result = LintResult()

    if not dsl.description:
        result.suggestions.append("Add a description to the template")
        result.score -= 10

    if len(dsl.variables) == 0:
        result.suggestions.append("Template has no variables — consider adding placeholders")
        result.score -= 5

    for v in dsl.variables:
        if not v.description:
            result.suggestions.append(f"Add description to variable '{v.name}'")
            result.score -= 2

        if v.required and v.default_value is None:
            result.suggestions.append(
                f"Required variable '{v.name}' has no default — users must always fill it"
            )

    if len(dsl.sections) == 0:
        result.suggestions.append("Template has no sections")
        result.score -= 15

    for section in dsl.sections:
        if len(section.body) < 50:
            result.suggestions.append(f"Section '{section.title}' seems very short")
            result.score -= 3

    result.score = max(0, result.score)
    return result
