# ContractForge AI-Native CLM — Makefile
# Works on Windows (cmd.exe / PowerShell) and Linux/macOS.
# Prerequisites: make, docker, docker compose, uv, powershell (PowerShell 7+)
#
# Quick start after clone:
#   make setup     — bootstrap everything once
#   make up        — start the stack
#   make down      — stop everything
#   make test      — run full test suite

UV      := uv
DC      := docker compose
PYTHON  := python
API_URL := http://localhost:8100

.PHONY: help setup up down restart nuke logs \
        migrate migrate-gen migrate-down seed \
        test test-unit test-e2e test-watch \
        lint fmt typecheck check clean

##── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo.
	@echo ContractForge AI-Native CLM
	@echo.
	@echo   make setup         Bootstrap everything (first run after clone)
	@echo   make up            Start all services in background
	@echo   make down          Stop containers (volumes kept)
	@echo   make restart       Restart api / worker / beat
	@echo   make nuke          Stop + delete all volumes (clean slate)
	@echo   make logs          Tail api / worker / beat logs
	@echo.
	@echo   make migrate       Apply pending DB migrations
	@echo   make seed          Load demo tenant + admin user
	@echo.
	@echo   make test          Full test suite with coverage
	@echo   make test-unit     Fast unit tests (no Docker needed)
	@echo   make test-e2e      End-to-end lifecycle tests
	@echo   make lint          Ruff linter
	@echo   make fmt           Ruff formatter + autofix
	@echo   make typecheck     mypy strict
	@echo   make check         lint + typecheck
	@echo   make clean         Remove __pycache__ and cache dirs
	@echo.

##── First-time setup ──────────────────────────────────────────────────────────
setup:
	@echo [1/5] Copying .env.example to .env (skip if exists)
	@powershell -NoProfile -NonInteractive -Command "if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env'; Write-Host '.env created' } else { Write-Host '.env already exists, skipping' }"
	@echo [2/5] Installing Python dependencies via uv
	$(UV) sync
	@echo [3/5] Starting Ollama (model pull takes a while on first run)
	$(DC) up -d ollama
	@powershell -NoProfile -NonInteractive -Command "Start-Sleep 8"
	$(DC) exec -T ollama ollama pull qwen2.5:14b
	$(DC) exec -T ollama ollama pull nomic-embed-text
	@echo [4/5] Starting full stack
	$(DC) up -d --build
	@echo Waiting for PostgreSQL to be ready...
	@powershell -NoProfile -NonInteractive -Command "Start-Sleep 10"
	@echo [5/5] Running database migrations
	$(DC) exec -T api alembic upgrade head
	@echo.
	@echo Done! Open $(API_URL)/api/docs
	@echo   Flower   -^> http://localhost:5556
	@echo   Grafana  -^> http://localhost:3002
	@echo   Langfuse -^> http://localhost:3003

##── Stack management ──────────────────────────────────────────────────────────
up:
	$(DC) up -d --build
	@echo Services started:
	@echo   API      -^> $(API_URL)
	@echo   Flower   -^> http://localhost:5556
	@echo   Grafana  -^> http://localhost:3002
	@echo   Langfuse -^> http://localhost:3003
	@echo   MinIO    -^> http://localhost:9010

down:
	$(DC) down

restart:
	$(DC) restart api worker beat

nuke:
	$(DC) down -v --remove-orphans

logs:
	$(DC) logs -f api worker beat

##── Database ──────────────────────────────────────────────────────────────────
migrate:
	$(DC) exec -T api alembic upgrade head

migrate-gen:
	$(DC) exec -T api alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	$(DC) exec -T api alembic downgrade -1

seed:
	$(DC) exec -T api $(PYTHON) scripts/seed_demo.py

##── Testing ───────────────────────────────────────────────────────────────────
test:
	$(UV) run pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=85 -x

test-unit:
	$(UV) run pytest tests/unit/ -v

test-e2e:
	$(UV) run pytest tests/e2e/ -v

test-watch:
	$(UV) run ptw tests/ src/ -- -v

##── Code quality ──────────────────────────────────────────────────────────────
lint:
	$(UV) run ruff check src/ tests/

fmt:
	$(UV) run ruff format src/ tests/
	$(UV) run ruff check --fix src/ tests/

typecheck:
	$(UV) run mypy src/

check: lint typecheck

##── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	@powershell -NoProfile -NonInteractive -Command "Get-ChildItem -Recurse -Directory -Filter __pycache__   | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
	@powershell -NoProfile -NonInteractive -Command "Get-ChildItem -Recurse -Directory -Filter .pytest_cache | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
	@powershell -NoProfile -NonInteractive -Command "Get-ChildItem -Recurse -Directory -Filter .mypy_cache   | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
	@powershell -NoProfile -NonInteractive -Command "Get-ChildItem -Recurse -File -Filter *.pyc             | Remove-Item -Force -ErrorAction SilentlyContinue"
	@echo Clean done.
