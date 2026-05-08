"""Parse template DSL from YAML/JSON into TemplateDSL model."""
from __future__ import annotations

import json

import structlog

from src.infrastructure.templates.dsl_models import TemplateDSL

log = structlog.get_logger(__name__)


def parse_dsl(raw: str) -> TemplateDSL:
    """Parse a DSL string (JSON or YAML) into a TemplateDSL model."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml
            data = yaml.safe_load(raw)
        except ImportError:
            raise ValueError("YAML parsing requires PyYAML package")
        except Exception as exc:
            raise ValueError(f"Failed to parse template DSL: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Template DSL must be a JSON/YAML object")

    return TemplateDSL.model_validate(data)
