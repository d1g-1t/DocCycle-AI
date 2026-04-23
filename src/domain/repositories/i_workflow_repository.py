from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.approval_decision import ApprovalDecision
from src.domain.entities.approval_stage import ApprovalStage
from src.domain.entities.approval_workflow import ApprovalWorkflow


class IWorkflowRepository(ABC):

    @abstractmethod
    async def get_workflow_by_id(self, workflow_id: UUID) -> ApprovalWorkflow | None: ...

    @abstractmethod
    async def get_workflow_by_contract(self, contract_id: UUID) -> ApprovalWorkflow | None: ...

    @abstractmethod
    async def save_workflow(self, workflow: ApprovalWorkflow) -> ApprovalWorkflow: ...

    @abstractmethod
    async def update_workflow(self, workflow: ApprovalWorkflow) -> ApprovalWorkflow: ...

    @abstractmethod
    async def list_stages(self, workflow_id: UUID) -> list[ApprovalStage]: ...

    @abstractmethod
    async def get_stage_by_id(self, stage_id: UUID) -> ApprovalStage | None: ...

    @abstractmethod
    async def save_stage(self, stage: ApprovalStage) -> ApprovalStage: ...

    @abstractmethod
    async def update_stage(self, stage: ApprovalStage) -> ApprovalStage: ...

    @abstractmethod
    async def save_decision(self, decision: ApprovalDecision) -> ApprovalDecision: ...

    @abstractmethod
    async def list_pending_workflows(self, offset: int = 0, limit: int = 50) -> list[ApprovalWorkflow]: ...
