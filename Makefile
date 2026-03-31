.PHONY: help install dev run test lint type-check format clean docker-up docker-down

# Default target
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install: ## Install production dependencies
	uv pip install -e .

dev: ## Install all dependencies (including dev tools)
	uv pip install -e ".[dev]"

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

run: ## Start dev server with auto-reload
	uv run python -m app.main

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=term-missing

lint: ## Run linter (ruff)
	ruff check app/ tests/

type-check: ## Run mypy type checker
	mypy app/

format: ## Auto-format code
	ruff format app/ tests/
	ruff check --fix app/ tests/

check: lint type-check test ## Run all checks (lint + types + tests)

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-up: ## Start local stack (Postgres + app)
	docker compose up -d

docker-down: ## Stop local stack
	docker compose down

docker-build: ## Build Docker image
	docker build -t fastapi-app .

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info/
