"""Workflow router — dynamically selects approval route based on contract attributes.

Unlike the pure-domain ``ApprovalRoutingService`` which returns a static
route, the *WorkflowRouter* enriches the route with tenant-specific
overrides (loaded from JSONB config), custom SLA policies, and
delegation/escalation settings.  It acts as the *infrastructure bridge*
between the domain routing table and the actual ``ApprovalWorkflow``
entity that gets persisted.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import structlog

from src.domain.entities.approval_stage import ApprovalStage
from src.domain.entities.approval_workflow import ApprovalWorkflow
from src.domain.services.approval_routing_service import ApprovalRoutingService, RouteStage

log = structlog.get_logger(__name__)


class WorkflowRouter:
    """Build a full ``ApprovalWorkflow`` from contract attributes."""

    def __init__(
        self,
        default_sla_hours: int = 24,
        enable_delegation: bool = True,
    ) -> None:
        self._default_sla_hours = default_sla_hours
        self._enable_delegation = enable_delegation

    async def create_workflow(
        self,
        contract_id: UUID,
        contract_type: str,
        amount: Decimal | None,
        tenant_overrides: dict | None = None,
    ) -> tuple[ApprovalWorkflow, list[ApprovalStage]]:
        """Compute route and build workflow + stage entities.

        Returns:
            Tuple of ``(workflow, stages)`` ready to be persisted.
        """
        route = ApprovalRoutingService.compute_route(contract_type, amount)
        route = self._apply_overrides(route, tenant_overrides or {})

        now = datetime.now(UTC)
        workflow = ApprovalWorkflow(
            id=uuid4(),
            contract_id=contract_id,
            current_stage_order=1,
            route_snapshot={
                "contract_type": contract_type,
                "amount": str(amount) if amount else None,
                "computed_at": now.isoformat(),
                "stages_count": len(route),
            },
            sla_policy={
                "default_sla_hours": self._default_sla_hours,
                "delegation_enabled": self._enable_delegation,
            },
        )

        stages: list[ApprovalStage] = []
        for rs in route:
            stage = ApprovalStage(
                id=uuid4(),
                workflow_id=workflow.id,
                stage_order=rs.stage_order,
                stage_type=rs.stage_type,
                assignee_role=rs.assignee_role,
                sla_hours=rs.sla_hours,
                status="IN_PROGRESS" if rs.stage_order == 1 else "PENDING",
                created_at=now,
            )
            stages.append(stage)

        log.info(
            "workflow_router.created",
            workflow_id=str(workflow.id),
            contract_id=str(contract_id),
            stages=len(stages),
        )
        return workflow, stages

    @staticmethod
    def _apply_overrides(
        route: list[RouteStage],
        overrides: dict,
    ) -> list[RouteStage]:
        """Apply tenant-specific overrides to the computed route.

        Supported override keys:
        - ``extra_stages``: list of dicts to append as extra stages.
        - ``sla_multiplier``: float multiplier for all SLA hours.
        - ``skip_types``: list of stage_types to remove.
        """
        # Remove skipped stage types
        skip = set(overrides.get("skip_types", []))
        if skip:
            route = [rs for rs in route if rs.stage_type not in skip]

        # Apply SLA multiplier
        multiplier = overrides.get("sla_multiplier")
        if multiplier is not None:
            for rs in route:
                rs.sla_hours = max(1, int(rs.sla_hours * float(multiplier)))

        # Append extra stages
        extras: list[dict] = overrides.get("extra_stages", [])
        base_order = max((rs.stage_order for rs in route), default=0)
        for i, extra in enumerate(extras, start=1):
            route.append(
                RouteStage(
                    stage_order=base_order + i,
                    stage_type=extra.get("stage_type", "CUSTOM"),
                    assignee_role=extra.get("assignee_role", "legal_counsel"),
                    sla_hours=extra.get("sla_hours", 24),
                )
            )

        return route
