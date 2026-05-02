"""SQLAlchemy playbook repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.playbook_rule import PlaybookRule
from src.domain.repositories.i_playbook_repository import IPlaybookRepository
from src.infrastructure.database.models.playbook_rule_model import PlaybookRuleModel


def _to_entity(m: PlaybookRuleModel) -> PlaybookRule:
    return PlaybookRule(
        id=m.id, tenant_id=m.tenant_id, contract_type=m.contract_type,
        rule_name=m.rule_name, severity=m.severity, rule_type=m.rule_type,
        condition_json=m.condition_json, explanation=m.explanation,
        fallback_clause_id=m.fallback_clause_id, is_active=m.is_active,
        version=m.version, created_at=m.created_at,
    )


class SqlPlaybookRepository(IPlaybookRepository):
    """Concrete playbook repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, rule_id: UUID, tenant_id: UUID) -> PlaybookRule | None:
        stmt = select(PlaybookRuleModel).where(
            PlaybookRuleModel.id == rule_id, PlaybookRuleModel.tenant_id == tenant_id,
        )
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def list_active_by_type(self, tenant_id: UUID, contract_type: str) -> list[PlaybookRule]:
        stmt = (
            select(PlaybookRuleModel)
            .where(
                PlaybookRuleModel.tenant_id == tenant_id,
                PlaybookRuleModel.contract_type == contract_type,
                PlaybookRuleModel.is_active.is_(True),
            )
            .order_by(PlaybookRuleModel.created_at)
        )
        rows = await self._session.scalars(stmt)
        return [_to_entity(r) for r in rows.all()]

    async def list_by_tenant(self, tenant_id: UUID, offset: int = 0, limit: int = 50) -> list[PlaybookRule]:
        stmt = (
            select(PlaybookRuleModel)
            .where(PlaybookRuleModel.tenant_id == tenant_id)
            .order_by(PlaybookRuleModel.created_at.desc())
            .offset(offset).limit(limit)
        )
        rows = await self._session.scalars(stmt)
        return [_to_entity(r) for r in rows.all()]

    async def save(self, rule: PlaybookRule) -> PlaybookRule:
        model = PlaybookRuleModel(
            id=rule.id, tenant_id=rule.tenant_id, contract_type=rule.contract_type,
            rule_name=rule.rule_name, severity=rule.severity, rule_type=rule.rule_type,
            condition_json=rule.condition_json, explanation=rule.explanation,
            fallback_clause_id=rule.fallback_clause_id, is_active=rule.is_active,
            version=rule.version,
        )
        self._session.add(model)
        await self._session.flush()
        return rule

    async def update(self, rule: PlaybookRule) -> PlaybookRule:
        stmt = select(PlaybookRuleModel).where(PlaybookRuleModel.id == rule.id)
        model = await self._session.scalar(stmt)
        if not model:
            raise ValueError(f"PlaybookRule {rule.id} not found")
        model.is_active = rule.is_active
        model.condition_json = rule.condition_json
        model.explanation = rule.explanation
        model.version = rule.version
        await self._session.flush()
        return rule
