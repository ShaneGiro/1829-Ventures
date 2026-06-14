# 1829 Ventures CRM — developer shortcuts.
.DEFAULT_GOAL := help
.PHONY: help up down logs build dev migrate revision lint format typecheck test test-cov backup shell

BACKEND := backend
COMPOSE := docker compose

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up: ## Start the full Docker Compose stack
	$(COMPOSE) up -d

down: ## Stop the stack
	$(COMPOSE) down

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

build: ## Rebuild images
	$(COMPOSE) build

dev: ## Run the API locally (expects local Postgres/Redis)
	cd $(BACKEND) && uvicorn app.main:app --reload

migrate: ## Apply migrations to head
	cd $(BACKEND) && alembic upgrade head

revision: ## Autogenerate a migration (usage: make revision m="message")
	cd $(BACKEND) && alembic revision --autogenerate -m "$(m)"

lint: ## Ruff lint
	cd $(BACKEND) && ruff check .

format: ## Ruff format
	cd $(BACKEND) && ruff format .

typecheck: ## mypy
	cd $(BACKEND) && mypy

test: ## Run tests
	cd $(BACKEND) && pytest

test-cov: ## Run tests with coverage report
	cd $(BACKEND) && pytest --cov=app --cov-report=term-missing

backup: ## Run the database backup script
	cd $(BACKEND) && bash scripts/backup_db.sh

shell: ## Open a shell in the running api container
	$(COMPOSE) exec api /bin/bash
