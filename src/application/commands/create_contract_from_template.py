from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.contract_dto import ContractResponse, CreateContractFromTemplateRequest
from src.application.interfaces.i_template_renderer import ITemplateRenderer
from src.domain.entities.contract import Contract
from src.domain.entities.contract_version import ContractVersion
from src.domain.exceptions import NotFoundError
from src.domain.value_objects.contract_status import ContractStatus
from src.domain.value_objects.contract_type import ContractType
from src.infrastructure.database.models.contract_model import ContractVersionModel
from src.infrastructure.database.repositories.sql_contract_repository import SqlContractRepository
from src.infrastructure.database.repositories.sql_template_repository import SqlTemplateRepository

log = structlog.get_logger(__name__)


class CreateContractFromTemplateCommand:

    def __init__(self, session: AsyncSession, renderer: ITemplateRenderer) -> None:
        self._contracts = SqlContractRepository(session)
        self._templates = SqlTemplateRepository(session)
        self._renderer = renderer
        self._session = session

    async def execute(
        self,
        req: CreateContractFromTemplateRequest,
        tenant_id: uuid.UUID,
        created_by: uuid.UUID,
    ) -> ContractResponse:
        version = await self._templates.get_version(req.template_version_id)
        if version is None:
            raise NotFoundError("TemplateVersion", str(req.template_version_id))

        rendered = await self._renderer.render(
            version.template_id, version.version_number, req.variables,
        )

        contract_id = uuid.uuid4()
        version_id = uuid.uuid4()
        now = datetime.now(UTC)
        content = rendered.html

        contract = Contract(
            id=contract_id,
            tenant_id=tenant_id,
            title=req.title,
            contract_type=ContractType(version.dsl.get("contract_type", "OTHER")),
            status=ContractStatus.DRAFT,
            current_version_id=version_id,
            template_id=version.template_id,
            counterparty_id=req.counterparty_id,
            amount=req.amount,
            currency=req.currency or "RUB",
            business_unit=req.business_unit,
            jurisdiction=req.jurisdiction,
            metadata={"template_version_id": str(req.template_version_id)},
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        cv = ContractVersion(
            id=version_id, contract_id=contract_id, version_number=1,
            source_type="TEMPLATE", content_text=content,
            checksum=hashlib.sha256(content.encode()).hexdigest(),
            redline_summary={"source": "template"}, created_by=created_by, created_at=now,
        )
        await self._contracts.save(contract)
        self._session.add(ContractVersionModel(
            id=cv.id, contract_id=cv.contract_id, version_number=cv.version_number,
            source_type=cv.source_type, content_text=cv.content_text,
            checksum=cv.checksum, redline_summary=cv.redline_summary,
            created_by=cv.created_by, created_at=cv.created_at,
        ))
        await self._session.flush()
        log.info("contract.created", contract_id=str(contract_id))
        return contract_to_response(contract)


def contract_to_response(c: Contract) -> ContractResponse:
    return ContractResponse(
        id=c.id, tenant_id=c.tenant_id, title=c.title,
        contract_type=c.contract_type.value, status=c.status.value,
        business_unit=c.business_unit, amount=c.amount, currency=c.currency,
        jurisdiction=c.jurisdiction, risk_score=c.risk_score,
        counterparty_id=c.counterparty_id, template_id=c.template_id,
        current_version_id=c.current_version_id, created_by=c.created_by,
        created_at=c.created_at, updated_at=c.updated_at,
    )
