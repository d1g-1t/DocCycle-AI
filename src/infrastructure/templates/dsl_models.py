"""Template DSL models — Pydantic schemas for template structure."""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class VariableType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTI_SELECT = "multi_select"


class TemplateVariable(BaseModel):
    """A variable placeholder in a template."""
    name: str = Field(min_length=1, max_length=128)
    label: str
    var_type: VariableType = VariableType.TEXT
    required: bool = True
    default_value: str | None = None
    options: list[str] = Field(default_factory=list)  # For SELECT/MULTI_SELECT
    description: str | None = None
    validation_regex: str | None = None


class TemplateSection(BaseModel):
    """A section within a template."""
    title: str
    body: str
    order: int = 0
    is_conditional: bool = False
    condition_variable: str | None = None


class TemplateDSL(BaseModel):
    """Top-level template DSL document."""
    name: str
    version: str = "1.0"
    description: str | None = None
    variables: list[TemplateVariable] = Field(default_factory=list)
    sections: list[TemplateSection] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
