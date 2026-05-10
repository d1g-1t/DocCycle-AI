"""Unit tests for template linter."""
from __future__ import annotations

from src.infrastructure.templates.dsl_models import TemplateDSL, TemplateSection, TemplateVariable, VariableType
from src.infrastructure.templates.template_linter import lint_template


def test_good_template_high_score():
    dsl = TemplateDSL(
        name="Good Template",
        description="A well-documented template",
        variables=[
            TemplateVariable(name="party_a", label="Party A", description="The first party"),
        ],
        sections=[
            TemplateSection(
                title="Introduction",
                body="This agreement is entered into by {{ party_a }} under the terms described herein.",
                order=1,
            ),
        ],
    )
    result = lint_template(dsl)
    assert result.score >= 80


def test_empty_template_low_score():
    dsl = TemplateDSL(name="Empty")
    result = lint_template(dsl)
    assert result.score < 80
    assert len(result.suggestions) > 0


def test_variable_without_description():
    dsl = TemplateDSL(
        name="Test",
        description="With desc",
        variables=[TemplateVariable(name="x", label="x")],
        sections=[TemplateSection(title="S", body="A" * 60, order=1)],
    )
    result = lint_template(dsl)
    assert any("description" in s.lower() for s in result.suggestions)
