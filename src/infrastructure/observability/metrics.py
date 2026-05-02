"""Prometheus custom metrics for ContractForge."""
from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge

# ── Contract lifecycle ────────────────────────────────────────────
contracts_created_total = Counter(
    "contractforge_contracts_created_total",
    "Total contracts created",
    ["tenant_id", "contract_type"],
)

contract_status_transitions_total = Counter(
    "contractforge_status_transitions_total",
    "Contract status transition count",
    ["from_status", "to_status"],
)

# ── AI pipeline ──────────────────────────────────────────────────
ai_review_duration_seconds = Histogram(
    "contractforge_ai_review_duration_seconds",
    "AI review pipeline duration",
    ["pipeline_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

ai_review_risk_score = Histogram(
    "contractforge_ai_review_risk_score",
    "Distribution of AI-computed risk scores",
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)

# ── Approval workflow ────────────────────────────────────────────
approval_workflows_active = Gauge(
    "contractforge_approval_workflows_active",
    "Currently active approval workflows",
)

approval_stage_duration_seconds = Histogram(
    "contractforge_approval_stage_duration_seconds",
    "Time spent in each approval stage",
    ["stage_type"],
)

# ── Obligations ──────────────────────────────────────────────────
obligations_overdue_total = Gauge(
    "contractforge_obligations_overdue_total",
    "Number of currently overdue obligations",
)

# ── Search ───────────────────────────────────────────────────────
search_queries_total = Counter(
    "contractforge_search_queries_total",
    "Total search queries executed",
    ["search_type"],
)

search_latency_seconds = Histogram(
    "contractforge_search_latency_seconds",
    "Search query latency",
    ["search_type"],
)
