.PHONY: help test test-unit test-bdd test-coverage test-watch format lint type-check clean install install-dev

help:
	@echo "GraphSQL Development Commands"
	@echo "============================="
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests (unit + BDD)"
	@echo "  make test-unit      - Run unit tests with pytest"
	@echo "  make test-bdd       - Run BDD tests with behave"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make test-watch     - Watch tests on file changes"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format         - Format code with black and ruff"
	@echo "  make lint           - Lint code with ruff"
	@echo "  make type-check     - Type checking with mypy"
	@echo ""
	@echo "Setup:"
	@echo "  make install        - Install package"
	@echo "  make install-dev    - Install with development dependencies"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Remove build and test artifacts"

test: test-unit test-bdd
	@echo "✅ All tests passed!"

test-unit:
	@echo "Running unit tests..."
	pytest -v

test-bdd:
	@echo "Running BDD tests..."
	behave

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-watch:
	@echo "Watching for test changes..."
	pytest-watch -- -v

format:
	@echo "Formatting code..."
	black src tests features
	ruff check --fix src tests

lint:
	@echo "Linting code..."
	ruff check src tests

type-check:
	@echo "Type checking..."
	mypy src

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf dist build *.egg-info
	rm -rf .behave/
