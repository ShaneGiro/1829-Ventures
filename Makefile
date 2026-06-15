# 1829 Ventures CRM — developer shortcuts.
.DEFAULT_GOAL := help

SHELL := /bin/bash

BACKEND := backend
FRONTEND := frontend
COMPOSE := docker compose
PYTHON ?= python3.12
VENV := $(BACKEND)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
ALEMBIC := $(VENV)/bin/alembic
UVICORN := $(VENV)/bin/uvicorn
CELERY := $(VENV)/bin/celery
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
PYTEST := $(VENV)/bin/pytest

.PHONY: help \
	check check-docker check-node check-python env setup install backend-install frontend-install \
	up up-build up-infra down restart logs logs-api logs-worker ps build shell \
	dev frontend-dev frontend-preview frontend-build frontend-lint frontend-typecheck frontend-test frontend-check frontend-gen-api \
	backend-dev backend-worker migrate revision lint format typecheck test test-cov backend-check backup clean

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

check: check-docker check-node check-python ## Verify required local tools are installed

check-docker: ## Verify Docker and Compose are available
	@command -v docker >/dev/null || { echo "Docker is required. Install Docker Desktop and retry."; exit 1; }
	@docker compose version >/dev/null || { echo "Docker Compose v2 is required. Install/update Docker Desktop and retry."; exit 1; }

check-node: ## Verify Node and npm are available
	@command -v node >/dev/null || { echo "Node.js 20+ is required."; exit 1; }
	@command -v npm >/dev/null || { echo "npm is required."; exit 1; }

check-python: ## Verify Python 3.12 is available
	@command -v $(PYTHON) >/dev/null || { echo "$(PYTHON) is required. Override with make PYTHON=/path/to/python."; exit 1; }

env: ## Create .env from .env.example if missing
	@test -f .env || cp .env.example .env

setup: env install ## Create .env and install backend/frontend dependencies

install: backend-install frontend-install ## Install backend and frontend dependencies

backend-install: check-python ## Create backend venv and install Python dependencies
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install torch --index-url https://download.pytorch.org/whl/cpu
	$(PIP) install -r $(BACKEND)/requirements.txt

frontend-install: check-node ## Install frontend npm dependencies when missing
	@if [ ! -d "$(FRONTEND)/node_modules" ]; then cd $(FRONTEND) && npm ci; fi

up: env check-docker ## Start Docker backend stack: Postgres, Redis, MinIO, API, worker
	$(COMPOSE) up -d

up-build: env check-docker ## Build and start the Docker backend stack
	$(COMPOSE) up -d --build

up-infra: env check-docker ## Start only Postgres, Redis, MinIO, and bucket init
	$(COMPOSE) up -d postgres redis minio minio-init

down: check-docker ## Stop the Docker stack
	$(COMPOSE) down

restart: down up ## Restart the Docker backend stack

logs: check-docker ## Tail logs for all Docker services
	$(COMPOSE) logs -f

logs-api: check-docker ## Tail API container logs
	$(COMPOSE) logs -f api

logs-worker: check-docker ## Tail Celery worker logs
	$(COMPOSE) logs -f worker

ps: check-docker ## Show Docker service status
	$(COMPOSE) ps

build: check-docker ## Rebuild Docker images
	$(COMPOSE) build

shell: check-docker ## Open a shell in the running API container
	$(COMPOSE) exec api /bin/bash

dev: up frontend-dev ## Start Docker backend stack, then run Vite frontend

frontend-dev: frontend-install ## Run the frontend dev server at http://localhost:5173
	cd $(FRONTEND) && npm run dev

frontend-preview: frontend-install ## Preview the built frontend
	cd $(FRONTEND) && npm run preview

frontend-build: frontend-install ## Build the frontend
	cd $(FRONTEND) && npm run build

frontend-lint: frontend-install ## Lint the frontend
	cd $(FRONTEND) && npm run lint

frontend-typecheck: frontend-install ## Typecheck the frontend
	cd $(FRONTEND) && npm run typecheck

frontend-test: frontend-install ## Run frontend tests
	cd $(FRONTEND) && npm test

frontend-check: frontend-lint frontend-typecheck frontend-test frontend-build ## Run all frontend checks

frontend-gen-api: frontend-install ## Regenerate frontend OpenAPI TypeScript types
	cd $(FRONTEND) && npm run gen:api

backend-dev: env backend-install up-infra migrate ## Run API locally at http://localhost:8000
	cd $(BACKEND) && ../$(UVICORN) app.main:app --reload

backend-worker: env backend-install up-infra ## Run Celery worker locally
	cd $(BACKEND) && ../$(CELERY) -A app.workers.celery_app.celery_app worker --loglevel=info

migrate: env backend-install ## Apply database migrations to head
	cd $(BACKEND) && ../$(PY) -m scripts.check_migration_state
	cd $(BACKEND) && ../$(ALEMBIC) upgrade head

revision: env backend-install ## Autogenerate a migration: make revision m="message"
	@test -n "$(m)" || { echo 'Usage: make revision m="message"'; exit 1; }
	cd $(BACKEND) && ../$(ALEMBIC) revision --autogenerate -m "$(m)"

lint: backend-install ## Ruff lint backend
	cd $(BACKEND) && ../$(RUFF) check .

format: backend-install ## Ruff format backend
	cd $(BACKEND) && ../$(RUFF) format .

typecheck: backend-install ## mypy typecheck backend
	cd $(BACKEND) && ../$(MYPY)

test: backend-install ## Run backend tests
	cd $(BACKEND) && ../$(PYTEST)

test-cov: backend-install ## Run backend tests with coverage
	cd $(BACKEND) && ../$(PYTEST) --cov=app --cov-report=term-missing

backend-check: lint typecheck test ## Run backend lint, typecheck, and tests

backup: backend-install ## Run the database backup script
	cd $(BACKEND) && bash scripts/backup_db.sh

clean: ## Remove generated frontend build/cache artifacts
	rm -rf $(FRONTEND)/dist $(FRONTEND)/.vite $(FRONTEND)/*.tsbuildinfo
