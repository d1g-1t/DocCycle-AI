"""Alembic initial migration — creates full schema matching SQL spec."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial"
down_revision: None = None
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "tenants",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "api_users",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "counterparties",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("inn", sa.String(12), nullable=True),
        sa.Column("ogrn", sa.String(15), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "contract_templates",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contract_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("current_version_id", sa.UUID, nullable=True),
        sa.Column("created_by", sa.UUID, sa.ForeignKey("api_users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "template_versions",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("template_id", sa.UUID, sa.ForeignKey("contract_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("dsl", sa.JSON, nullable=False),
        sa.Column("variables", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("render_policy", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("checksum", sa.String(64), nullable=False, server_default=""),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID, sa.ForeignKey("api_users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("template_id", "version_number"),
    )

    op.create_foreign_key(
        "fk_contract_templates_current_version",
        "contract_templates", "template_versions",
        ["current_version_id"], ["id"],
    )

    op.create_table(
        "clause_library_entries",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("canonical_text", sa.Text, nullable=False),
        sa.Column("fallback_text", sa.Text, nullable=True),
        sa.Column("risk_level", sa.String(32), nullable=False, server_default="LOW"),
        sa.Column("tags", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("created_by", sa.UUID, sa.ForeignKey("api_users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "playbook_rules",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("contract_type", sa.String(64), nullable=False),
        sa.Column("rule_name", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("rule_type", sa.String(64), nullable=False),
        sa.Column("condition_json", sa.JSON, nullable=False),
        sa.Column("explanation", sa.Text, nullable=False, server_default=""),
        sa.Column("fallback_clause_id", sa.UUID, sa.ForeignKey("clause_library_entries.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "contracts",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("counterparty_id", sa.UUID, sa.ForeignKey("counterparties.id"), nullable=True),
        sa.Column("template_id", sa.UUID, sa.ForeignKey("contract_templates.id"), nullable=True),
        sa.Column("current_version_id", sa.UUID, nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("contract_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("business_unit", sa.String(128), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("jurisdiction", sa.String(128), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_by", sa.UUID, sa.ForeignKey("api_users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "contract_versions",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", sa.UUID, sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("content_text", sa.Text, nullable=False),
        sa.Column("rendered_file_path", sa.String(512), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("redline_summary", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("extracted_metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_by", sa.UUID, sa.ForeignKey("api_users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("contract_id", "version_number"),
    )

    op.create_foreign_key(
        "fk_contracts_current_version",
        "contracts", "contract_versions",
        ["current_version_id"], ["id"],
    )

    op.create_table(
        "contract_attachments",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_version_id", sa.UUID, sa.ForeignKey("contract_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", sa.UUID, sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("current_stage_order", sa.Integer, nullable=False, server_default="1"),
        sa.Column("route_snapshot", sa.JSON, nullable=False),
        sa.Column("sla_policy", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "approval_stages",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_id", sa.UUID, sa.ForeignKey("approval_workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage_order", sa.Integer, nullable=False),
        sa.Column("stage_type", sa.String(64), nullable=False),
        sa.Column("assignee_user_id", sa.UUID, sa.ForeignKey("api_users.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("due_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("escalation_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
    )

    op.create_table(
        "approval_decisions",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("stage_id", sa.UUID, sa.ForeignKey("approval_stages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("decided_by", sa.UUID, sa.ForeignKey("api_users.id"), nullable=False),
        sa.Column("decided_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "contract_obligations",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", sa.UUID, sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contract_version_id", sa.UUID, sa.ForeignKey("contract_versions.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("responsible_role", sa.String(64), nullable=True),
        sa.Column("responsible_user_id", sa.UUID, sa.ForeignKey("api_users.id"), nullable=True),
        sa.Column("due_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("renewal_window_start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("renewal_window_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("penalty_text", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "reminder_events",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("obligation_id", sa.UUID, sa.ForeignKey("contract_obligations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reminder_type", sa.String(32), nullable=False),
        sa.Column("scheduled_for", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
    )

    op.create_table(
        "search_embeddings",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.UUID, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "ai_analysis_runs",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("contract_id", sa.UUID, sa.ForeignKey("contracts.id"), nullable=True),
        sa.Column("contract_version_id", sa.UUID, sa.ForeignKey("contract_versions.id"), nullable=True),
        sa.Column("pipeline_type", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("input_snapshot", sa.JSON, nullable=False),
        sa.Column("output_snapshot", sa.JSON, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("prompt_tokens", sa.Integer, nullable=True),
        sa.Column("completion_tokens", sa.Integer, nullable=True),
        sa.Column("trace_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "audit_entries",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("actor_user_id", sa.UUID, sa.ForeignKey("api_users.id"), nullable=True),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.UUID, nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("trace_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # Indexes
    op.create_index("idx_templates_tenant_type", "contract_templates", ["tenant_id", "contract_type"])
    op.create_index("idx_contracts_tenant_status", "contracts", ["tenant_id", "status"])
    op.create_index("idx_contracts_counterparty", "contracts", ["counterparty_id"])
    op.create_index("idx_approval_workflows_status", "approval_workflows", ["status"])
    op.create_index("idx_approval_stages_due", "approval_stages", ["status", "due_at"])
    op.create_index("idx_obligations_due", "contract_obligations", ["status", "due_date"])
    op.create_index("idx_reminders_scheduled", "reminder_events", ["status", "scheduled_for"])
    op.create_index("idx_ai_analysis_pipeline", "ai_analysis_runs", ["pipeline_type", "created_at"])

    op.execute("""
        CREATE INDEX idx_clause_library_embedding_hnsw
        ON clause_library_entries
        USING hnsw (embedding vector_cosine_ops)
    """)
    op.execute("""
        CREATE INDEX idx_search_embeddings_hnsw
        ON search_embeddings
        USING hnsw (embedding vector_cosine_ops)
    """)
    op.execute("""
        CREATE INDEX idx_search_embeddings_fts
        ON search_embeddings
        USING GIN (to_tsvector('russian', content))
    """)
    op.execute("""
        CREATE INDEX idx_search_embeddings_metadata_gin
        ON search_embeddings USING GIN (metadata)
    """)
    op.execute("""
        CREATE INDEX idx_contracts_metadata_gin
        ON contracts USING GIN (metadata)
    """)


def downgrade() -> None:
    tables = [
        "audit_entries", "ai_analysis_runs", "search_embeddings",
        "reminder_events", "contract_obligations", "approval_decisions",
        "approval_stages", "approval_workflows", "contract_attachments",
        "contract_versions", "contracts", "playbook_rules",
        "clause_library_entries", "template_versions", "contract_templates",
        "counterparties", "api_users", "tenants",
    ]
    for table in tables:
        op.drop_table(table)
