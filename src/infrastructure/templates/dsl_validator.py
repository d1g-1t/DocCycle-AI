"""Validate template DSL: check variables, references, and structure."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.infrastructure.templates.dsl_models import TemplateDSL


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_dsl(dsl: TemplateDSL) -> ValidationResult:
    """Validate a parsed TemplateDSL for consistency and completeness."""
    result = ValidationResult()
    defined_vars = {v.name for v in dsl.variables}

    # Check for duplicate variable names
    seen_names: set[str] = set()
    for v in dsl.variables:
        if v.name in seen_names:
            result.errors.append(f"Duplicate variable name: '{v.name}'")
            result.is_valid = False
        seen_names.add(v.name)

    # Check variable references in sections
    for section in dsl.sections:
        refs = set(re.findall(r"\{\{\s*(\w+)\s*\}\}", section.body))
        undefined = refs - defined_vars
        if undefined:
            result.errors.append(
                f"Section '{section.title}' references undefined variables: {undefined}"
            )
            result.is_valid = False

        # Check conditional variables
        if section.is_conditional and section.condition_variable:
            if section.condition_variable not in defined_vars:
                result.errors.append(
                    f"Section '{section.title}' condition references undefined variable: "
                    f"'{section.condition_variable}'"
                )
                result.is_valid = False

    # Warnings
    used_vars: set[str] = set()
    for section in dsl.sections:
        used_vars.update(re.findall(r"\{\{\s*(\w+)\s*\}\}", section.body))
    unused = defined_vars - used_vars
    for v in unused:
        result.warnings.append(f"Variable '{v}' is defined but never referenced in any section")

    return result
