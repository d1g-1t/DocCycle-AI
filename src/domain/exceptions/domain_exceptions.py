from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class NotFoundError(DomainError):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(f"{resource} with id={resource_id} not found")
        self.resource = resource
        self.resource_id = resource_id


class AccessDeniedError(DomainError):
    """Caller is not authorized to perform this action."""


class InvalidStatusTransitionError(DomainError):
    """Attempted invalid contract / workflow status transition."""


class DuplicateResourceError(DomainError):
    """Resource already exists (e.g. duplicate template version)."""


class PlaybookViolationError(DomainError):
    """Playbook check failed — mandatory clause missing or deviation."""

    def __init__(self, violations: list[str]) -> None:
        super().__init__(f"Playbook violations: {', '.join(violations)}")
        self.violations = violations


class TemplateRenderError(DomainError):
    """Template rendering failed due to missing variables or DSL error."""


class AiPipelineError(DomainError):
    """AI pipeline returned invalid or empty result."""
