# ContractForge AI-Native CLM

> AI-powered contract lifecycle management for people who don't want to read 47-page PDFs manually.

Self-hosted, multi-tenant, async-first — built with FastAPI, PostgreSQL, Redis, Ollama and a healthy dose of DDD.

---

## What's inside

| Layer | Tech |
|---|---|
| API | FastAPI 0.115 + Pydantic v2 |
| DB | PostgreSQL 16 + pgvector + pg_trgm |
| ORM | SQLAlchemy 2 async (`asyncpg`) |
| Migrations | Alembic (async) |
| Queue | Redis 7 + Celery 5 + Flower |
| AI | Ollama (qwen2.5:14b + nomic-embed-text) + LangChain |
| Auth | PASETO v4.local tokens + bcrypt |
| Files | MinIO (S3-compatible) |
| Search | pgvector cosine + pg_trgm FTS hybrid, MMR re-ranking |
| Document Parsing | unstructured (PDF/DOCX), custom clause splitter |
| Templates | Jinja2 + custom DSL with linter/validator |
| Notifications | Email (SMTP) / Telegram / Webhook |
| Observability | OpenTelemetry → Tempo, Prometheus → Grafana, Langfuse, Loki |

All ports are deliberately **non-standard** so this stack lives happily alongside whatever else you're running.

| Service | Host Port | Container Port |
|---|---|---|
| API | **8100** | 8000 |
| PostgreSQL | **5433** | 5432 |
| Redis | **6380** | 6379 |
| Ollama | **11435** | 11434 |
| MinIO API | **9010** | 9000 |
| MinIO Console | **9011** | 9001 |
| Flower | **5556** | 5555 |
| Prometheus | **9091** | 9090 |
| Grafana | **3002** | 3000 |
| Langfuse | **3003** | 3000 |
| Tempo (OTLP gRPC) | **4318** | 4317 |
| Tempo (HTTP) | **3201** | 3200 |
| Loki | **3101** | 3100 |

---

## Getting started

You need: `docker`, `docker compose`, `python 3.12`, `uv` (`pip install uv`).

```bash
# Clone and boot everything — one command, seriously
make setup
```

That will:
1. Copy `.env.example` → `.env`
2. Install Python deps via `uv sync`
3. Pull Ollama models (`qwen2.5:14b` and `nomic-embed-text`) — this takes a few minutes on first run
4. Start the full Docker Compose stack
5. Run database migrations

After that, check out the interactive docs at **http://localhost:8100/api/docs**.

### Other make targets

```bash
make up          # start everything in background
make down        # stop everything (data kept)
make restart     # down + up
make nuke        # stop + delete volumes — clean slate

make test        # run full test suite with coverage
make test-unit   # just the fast unit tests (no docker needed)
make lint        # ruff check
make fmt         # ruff format + fix
make typecheck   # mypy strict
make check       # lint + typecheck + test — run before PRs

make migrate           # apply pending db migrations
make migrate-gen MSG="add signatory table"  # generate new migration
make seed              # load demo tenant + admin user

make logs        # tail api/worker/beat logs
make clean       # remove __pycache__ and .pyc files
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation Layer                                              │
│  FastAPI routers · middleware · SSE · WebSocket                   │
├─────────────────────────────────────────────────────────────────┤
│  Application Layer                                               │
│  Commands (writes) · Queries (reads) · Use Cases · DTOs          │
├─────────────────────────────────────────────────────────────────┤
│  Domain Layer  (zero infra imports)                              │
│  Entities · Value Objects · Domain Services · Repository I/F     │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                            │
│  PostgreSQL · Redis · MinIO · Ollama · Celery · SMTP · Telegram  │
└─────────────────────────────────────────────────────────────────┘
```

**DDD + CQRS + Hexagonal (Ports-and-Adapters)**. The domain layer defines repository interfaces; the infrastructure layer provides implementations. You can swap PostgreSQL for MongoDB without touching a single domain file.

---

## Project layout

```
src/
├── core/                  # Config, structured logging, telemetry, security, DI container
│   ├── config.py          # Pydantic Settings with all env vars + non-standard ports
│   ├── logging.py         # structlog → JSON, shipped to Loki
│   ├── telemetry.py       # OpenTelemetry → Tempo traces + Prometheus metrics
│   ├── security.py        # PASETO token creation/verification
│   └── container.py       # dependency-injector wiring
│
├── domain/                # Pure business logic — no framework imports allowed
│   ├── entities/          # Contract, Template, Workflow, Obligation, etc. (14 entities)
│   ├── value_objects/     # ContractStatus, Money, ClauseType, RiskLevel, etc. (8 VOs)
│   ├── services/          # ContractRiskService, PlaybookEvaluator, etc. (5 services)
│   ├── repositories/      # Abstract interfaces for all persistence (7 repos)
│   └── exceptions/        # DomainException hierarchy
│
├── application/           # Orchestration — thin, delegates to domain
│   ├── commands/          # Write operations (8 commands)
│   ├── queries/           # Read operations (6 queries)
│   ├── use_cases/         # Complex multi-step scenarios (4 use cases)
│   ├── dto/               # Pydantic request/response models (6 DTOs)
│   └── interfaces/        # Port interfaces for infra adapters (5 interfaces)
│
├── infrastructure/        # Everything that talks to the outside world
│   ├── ai/                # Ollama LLM + embedding adapters
│   │   ├── ollama_llm_service.py
│   │   ├── ollama_embedding_service.py
│   │   ├── contract_review_pipeline.py   # LangChain-based multi-step review
│   │   ├── prompts/                      # Structured AI prompt templates
│   │   ├── pipelines/                    # Obligation extraction pipeline
│   │   ├── evaluators/                   # Review quality evaluator
│   │   └── services/                     # Prompt loader service
│   ├── cache/             # Redis cache (get/set/delete/invalidate_pattern)
│   ├── database/
│   │   ├── models/        # SQLAlchemy 2.0 mapped classes (15 models)
│   │   ├── repositories/  # SQL implementations of domain repos (7 repos)
│   │   ├── migrations/    # Alembic async migrations
│   │   └── session.py     # async_session_factory + get_session dependency
│   ├── notifications/     # Email (SMTP) + Telegram + Webhook notifiers
│   ├── observability/     # Prometheus metrics, OpenTelemetry tracing, Langfuse
│   ├── parsing/           # PDF/DOCX/HTML extractor, clause splitter, chunker
│   ├── queue/             # Celery app + 9 async tasks (4 beat schedules)
│   ├── search/            # pgvector + pg_trgm hybrid search, MMR re-ranking
│   ├── security/          # PASETO service, bcrypt hasher, RBAC engine
│   ├── storage/           # MinIO S3 adapter
│   ├── templates/         # Jinja2 renderer + DSL parser/validator/linter
│   └── workflows/         # Approval engine, SLA policy, delegation (DB-backed), escalation, routing
│
├── presentation/
│   ├── routers/           # 11 FastAPI routers (auth, contracts, templates, etc.)
│   ├── middleware/        # request-id, security headers, rate limiting
│   ├── sse/               # Server-Sent Events for live workflow updates
│   ├── websockets/        # WebSocket for AI review streaming
│   ├── deps.py            # Shared FastAPI dependencies (auth, tenant, pagination)
│   └── exception_handlers.py
│
└── main.py                # App factory with all routers, middleware, lifespan

tests/
├── conftest.py            # Async SQLite fixtures + FastAPI test client
├── unit/                  # 13 test files — pure logic, no I/O, < 5 seconds
├── integration/           # HTTP-level tests via httpx.AsyncClient
└── e2e/                   # Full lifecycle tests (health → auth → CRUD → review → approval)
```

---

## Key design decisions

**N+1 prevention** — all SQLAlchemy relationships use `lazy="noload"` by default. Repositories load what they need explicitly with `selectinload()`. `ApprovalWorkflowModel.stages` is the only eager exception because they're always needed together.

**CQRS** — write operations go through `commands/`, read operations through `queries/`. Both are thin orchestrators; the actual rules live in the domain layer.

**Async everywhere** — `asyncpg` for DB, `httpx` for Ollama calls, `asyncio.to_thread` for the synchronous MinIO SDK. Celery tasks use `asyncio.run()` to bridge into the sync world (compatible with Python 3.12+; switch to `taskiq` if you need native async workers).

**PASETO tokens** — v4.local symmetric encryption, safer than JWT for intranet-trust scenarios. `pyseto` handles the crypto.

**Multi-tenancy** — every query is scoped by `tenant_id`. There's no global query filter magic; it's explicit in every repository method so you can see exactly what's happening.

**RBAC** — role hierarchy `viewer < editor < approver < admin < super_admin`. The RBAC engine checks minimum required roles per endpoint. Roles are stored on the user entity and verified in FastAPI deps.

**Hybrid search** — vector similarity via pgvector (cosine distance) combined with full-text search via pg_trgm. Results are re-ranked using Maximal Marginal Relevance (MMR) to ensure diversity while maintaining relevance.

**Template DSL** — contract templates use a custom DSL with typed variables (`{{party_name:string}}`, `{{amount:money}}`). A parser, validator, and linter ensure templates are well-formed before publishing.

---

## AI pipeline

```
Upload/Create Contract
        │
        ▼
  ┌──────────────┐
  │ File Extract  │  PDF / DOCX / HTML → plain text
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ Chunking     │  Split into semantic chunks (512 tokens, 64 overlap)
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ Embedding    │  nomic-embed-text → pgvector (1536-dim)
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ AI Review    │  qwen2.5:14b via LangChain structured output
  │              │  → risks, missing clauses, non-standard terms
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ Obligations  │  Extract deadlines, payment terms, renewal dates
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │ Playbook     │  Evaluate against risk scoring rules
  └──────────────┘
```

All AI tasks run asynchronously via Celery queues (`clm.ai`, `clm.parse`). Real-time progress is streamed to the frontend via WebSocket at `/ws/review/{contract_id}`.

---

## Real-time endpoints

| Type | Path | Description |
|---|---|---|
| SSE | `GET /api/v1/events/workflows/{id}` | Live approval workflow status updates |
| WebSocket | `WS /ws/review/{contract_id}` | AI review progress streaming |

SSE uses Redis pub/sub under the hood. The WebSocket endpoint streams structured JSON messages as each AI pipeline step completes.

---

## API overview

### Auth & Health

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Get PASETO access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh token pair |
| GET | `/api/v1/auth/me` | Current user profile |
| GET | `/api/v1/health` | Health check (DB + Redis + Ollama status) |

### Contracts

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/contracts` | List contracts (paginated, filterable by status/counterparty) |
| POST | `/api/v1/contracts` | Create contract from template |
| GET | `/api/v1/contracts/{id}` | Full contract detail with versions |
| POST | `/api/v1/contracts/{id}/archive` | Archive contract (with guard rails) |

### Templates

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/templates` | Create contract template (with DSL validation) |
| POST | `/api/v1/templates/{id}/versions` | Publish new template version |

### AI Review

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/contracts/{id}/review` | Trigger AI review (async, returns `run_id`) |
| GET | `/api/v1/review/{run_id}` | Get AI review results |

### Approval Workflows

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/workflows` | Start approval workflow for a contract |
| POST | `/api/v1/workflows/{id}/stages/{sid}/approve` | Approve a stage |
| POST | `/api/v1/workflows/{id}/stages/{sid}/reject` | Reject a stage |

### Obligations

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/obligations/dashboard` | Obligation calendar with upcoming deadlines |

### Files

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/files/contracts/upload` | Upload incoming third-party contract (PDF/DOCX) |

### Search

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/search` | Hybrid semantic + full-text contract search |

### Playbooks

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/playbooks` | List risk playbook rules |
| POST | `/api/v1/playbooks` | Create playbook rule |

### Analytics

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/analytics/cycle-time` | Contract lifecycle timing analytics |

Full interactive spec lives at **http://localhost:8100/api/docs** once the stack is running.

---

## Celery tasks & beat schedule

| Task | Queue | Schedule |
|---|---|---|
| `ai_review` | `clm.ai` | on-demand |
| `embedding` | `clm.ai` | on-demand |
| `obligation_extraction` | `clm.ai` | on-demand |
| `negotiation_summary` | `clm.ai` | on-demand |
| `parse_uploaded_contract` | `clm.parse` | on-demand |
| `reminder` | `clm.workflow` | **every 60 min** |
| `workflow_sla_monitor` | `clm.workflow` | **every 15 min** |
| `analytics_refresh` | `clm.analytics` | **every 30 min** |
| `cleanup_orphan_files` | `clm.maintenance` | **daily 03:00** |

---

## Sample contracts

The `sample_contracts/` directory contains ready-to-load data:

- `templates/` — NDA and service agreement templates with typed variables (RU jurisdiction)
- `incoming/` — example incoming third-party contract (HTML) with red-flag annotations
- `playbooks/` — risk evaluation rules with preferred/acceptable/unacceptable positions

Use `make seed` to load demo data, or import the JSON files via the API.

---

## Middleware

| Middleware | Purpose |
|---|---|
| `RequestIdMiddleware` | Generates `X-Request-ID` header, propagates through logs and traces |
| `SecurityHeadersMiddleware` | Sets `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, CSP |
| `RateLimitMiddleware` | Redis-backed sliding window rate limiting per IP |
| CORS | Configurable origins via `CORS_ORIGINS` env var |

---

## Environment variables

Copy `.env.example` and fill in secrets. The most important ones:

```env
SECRET_KEY=            # 32+ bytes, used for PASETO token encryption
DB_PASSWORD=           # Postgres password (default: cf-secret-2026)
MINIO_ROOT_PASSWORD=   # MinIO password (default: minio-secret-2026)
REDIS_PASSWORD=        # Redis password (default: cf-redis-secret)
LANGFUSE_SECRET_KEY=   # Langfuse tracing key
```

Everything else has sane defaults for local dev. See `.env.example` for the full list.

---

## Running tests

### Without Docker (unit tests)

Unit tests don't need Postgres or Redis — they test pure domain logic:

```bash
uv sync
make test-unit
# or: uv run pytest tests/unit/ -v
```

### Full test suite

Integration tests use SQLite in-memory (via `aiosqlite`) and mock external services:

```bash
make test
# runs: uv run pytest --cov=src --cov-report=term-missing -v
```

### What's tested

- **Domain entities**: contract state machine transitions, obligation deadlines, risk calculations
- **Value objects**: money arithmetic, clause types, approval actions
- **Domain services**: playbook evaluation, contract risk scoring
- **Infrastructure**: clause splitter, contract chunker, document normalizer, template DSL
- **Security**: RBAC role hierarchy, permission checks
- **Search**: MMR re-ranking, snippet building
- **SLA**: policy evaluation, deadline calculations
- **Integration**: health endpoint, auth flow

---

## Observability stack

- **Grafana** at http://localhost:3002 — pre-provisioned datasources for Prometheus, Tempo, and Loki
- **Prometheus** at http://localhost:9091 — FastAPI request metrics via `prometheus-fastapi-instrumentator`; custom gauges for active contracts, pending reviews, queue depth
- **Tempo** — distributed traces from OpenTelemetry, visible in Grafana's Explore view
- **Loki** at http://localhost:3101 — structured JSON logs from `structlog`, queryable via LogQL
- **Langfuse** at http://localhost:3003 — LLM call tracing (prompt tokens, latency, model, cost estimation)
- **Flower** at http://localhost:5556 — Celery queue monitoring and task inspection

---

## Docker services

The `docker-compose.yml` runs 13 services:

| Service | Image | Role |
|---|---|---|
| `api` | custom (Dockerfile) | FastAPI application server |
| `worker` | custom (Dockerfile) | Celery worker (queues: `clm.parse`, `clm.ai`, `clm.workflow`, `clm.analytics`, `clm.maintenance`) |
| `beat` | custom (Dockerfile) | Celery Beat scheduler for periodic tasks |
| `postgres` | postgres:16-alpine | Primary database with pgvector + pg_trgm |
| `redis` | redis:7-alpine | Cache + Celery broker + pub/sub for SSE |
| `ollama` | ollama/ollama | Local LLM inference server |
| `ollama-init` | ollama/ollama | One-shot model puller (qwen2.5:14b + nomic-embed-text) |
| `minio` | minio/minio | S3-compatible file storage |
| `flower` | mher/flower:2.0 | Celery monitoring dashboard |
| `prometheus` | prom/prometheus | Metrics collection |
| `tempo` | grafana/tempo | Distributed tracing backend |
| `loki` | grafana/loki | Log aggregation |
| `grafana` | grafana/grafana | Dashboards and visualization |
| `langfuse` | langfuse/langfuse | LLM observability platform |

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and PR:

1. **Lint** — `ruff check` + `ruff format --check`
2. **Type check** — `mypy --strict`
3. **Test** — `pytest` with coverage report
4. **Security** — `pip-audit` for known vulnerabilities

---

## Contributing

PRs welcome. Run `make check` before opening one — it enforces `ruff` + `mypy strict` + full test suite. `type: ignore` is your enemy.

---

## License

Private. All rights reserved.
