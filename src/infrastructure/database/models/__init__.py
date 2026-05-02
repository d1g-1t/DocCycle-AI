"""ORM models barrel — import ALL models here so Alembic can discover them."""

from src.infrastructure.database.models.ai_analysis_run_model import AiAnalysisRunModel
from src.infrastructure.database.models.api_user_model import ApiUserModel
from src.infrastructure.database.models.approval_workflow_model import (
    ApprovalDecisionModel,
    ApprovalStageModel,
    ApprovalWorkflowModel,
)
from src.infrastructure.database.models.audit_entry_model import AuditEntryModel
from src.infrastructure.database.models.clause_library_entry_model import ClauseLibraryEntryModel
from src.infrastructure.database.models.contract_attachment_model import ContractAttachmentModel
from src.infrastructure.database.models.contract_model import ContractModel, ContractVersionModel
from src.infrastructure.database.models.contract_obligation_model import ContractObligationModel
from src.infrastructure.database.models.contract_template_model import (
    ContractTemplateModel,
    TemplateVersionModel,
)
from src.infrastructure.database.models.counterparty_model import CounterpartyModel
from src.infrastructure.database.models.delegation_model import DelegationModel
from src.infrastructure.database.models.playbook_rule_model import PlaybookRuleModel
from src.infrastructure.database.models.reminder_event_model import ReminderEventModel
from src.infrastructure.database.models.search_embedding_model import SearchEmbeddingModel
from src.infrastructure.database.models.tenant_model import TenantModel

__all__ = [
    "AiAnalysisRunModel",
    "ApiUserModel",
    "ApprovalDecisionModel",
    "ApprovalStageModel",
    "ApprovalWorkflowModel",
    "AuditEntryModel",
    "ClauseLibraryEntryModel",
    "ContractAttachmentModel",
    "ContractModel",
    "ContractObligationModel",
    "ContractTemplateModel",
    "ContractVersionModel",
    "CounterpartyModel",
    "DelegationModel",
    "PlaybookRuleModel",
    "ReminderEventModel",
    "SearchEmbeddingModel",
    "TenantModel",
    "TemplateVersionModel",
]
