.PHONY: help install dev test test-unit test-bdd test-coverage test-watch lint type-check format clean docker-build docker-run serve inspect quality deno-lint deno-fmt docs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install package
	uv pip install -e .

dev: ## Install package with dev dependencies
	uv pip install -e ".[dev]"
	pre-commit install

test: test-unit test-bdd ## Run all tests (unit + BDD)
	@echo "✅ All tests passed!"

test-unit: ## Run unit tests with pytest
	@echo "Running unit tests..."
	pytest -v

test-bdd: ## Run BDD tests with behave
	@echo "Running BDD tests..."
	behave

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-watch: ## Watch tests on file changes
	@echo "Watching for test changes..."
	pytest-watch -- -v

lint: ## Run linters
	ruff check src/
	mypy src/

type-check: ## Type checking with mypy
	mypy src/

deno-lint: ## Lint TypeScript/Fresh admin
	deno lint admin

deno-fmt: ## Format TypeScript/Fresh admin
	deno fmt admin

format: ## Format code (Python + TypeScript)
	black src/
	ruff check src/ --fix
	deno fmt admin

docs: ## Build Sphinx documentation
	sphinx-build -b html docs docs/_build
	@echo "📚 Documentation built in docs/_build/"

quality: lint deno-lint test docs ## Run complete quality check (lint, test, docs)
	@echo "✅ Quality check passed!"

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf dist build *.egg-info
	rm -rf .behave/

docker-build: ## Build Docker image
	docker build -t graphsql:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env graphsql:latest

serve: ## Start development server
	graphsql server --reload

inspect: ## Inspect database
	graphsql inspect