"""Unit tests for template DSL validation."""
from __future__ import annotations

import pytest

from src.infrastructure.templates.dsl_models import TemplateDSL, TemplateSection, TemplateVariable, VariableType
from src.infrastructure.templates.dsl_validator import validate_dsl


def test_valid_dsl_passes():
    dsl = TemplateDSL(
        name="Test",
        variables=[TemplateVariable(name="party_a", label="Party A", var_type=VariableType.TEXT)],
        sections=[TemplateSection(title="Intro", body="Welcome {{ party_a }}!", order=1)],
    )
    result = validate_dsl(dsl)
    assert result.is_valid is True
    assert result.errors == []


def test_undefined_variable_reference():
    dsl = TemplateDSL(
        name="Test",
        variables=[],
        sections=[TemplateSection(title="Intro", body="Welcome {{ unknown_var }}!", order=1)],
    )
    result = validate_dsl(dsl)
    assert result.is_valid is False
    assert any("undefined variables" in e.lower() for e in result.errors)


def test_duplicate_variable_names():
    dsl = TemplateDSL(
        name="Test",
        variables=[
            TemplateVariable(name="x", label="X"),
            TemplateVariable(name="x", label="X again"),
        ],
        sections=[],
    )
    result = validate_dsl(dsl)
    assert result.is_valid is False
    assert any("duplicate" in e.lower() for e in result.errors)


def test_unused_variable_produces_warning():
    dsl = TemplateDSL(
        name="Test",
        variables=[TemplateVariable(name="unused_var", label="Unused")],
        sections=[TemplateSection(title="Body", body="No variables here.", order=1)],
    )
    result = validate_dsl(dsl)
    assert result.is_valid is True
    assert any("unused_var" in w for w in result.warnings)


def test_conditional_section_with_invalid_variable():
    dsl = TemplateDSL(
        name="Test",
        variables=[],
        sections=[TemplateSection(
            title="Optional", body="Text", order=1,
            is_conditional=True, condition_variable="nonexistent",
        )],
    )
    result = validate_dsl(dsl)
    assert result.is_valid is False
