# Smart Fashion - Makefile
# Simplifies common development commands

.PHONY: help install dev run dev-app dev-worker test test-cov test-cov-html test-level1 test-level2 test-level3 test-level4 \
        format lint fix docker-up docker-down docker-logs docker-build clean

# Default target
help:
	@echo "Smart Fashion - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install        Install dependencies with Poetry"
	@echo ""
	@echo "Development:"
	@echo "  make dev            Start full local demo stack (app + worker + mysql)"
	@echo "  make run            Alias for 'make dev'"
	@echo "  make dev-app        Start only FastAPI app with uvicorn"
	@echo "  make dev-worker     Start only background worker"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-cov       Run tests with coverage report"
	@echo "  make test-level1    Run local infrastructure/config tests"
	@echo "  make test-level2    Run service tests"
	@echo "  make test-level3    Run API tests"
	@echo "  make test-level4    Run UI tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format         Format code with ruff"
	@echo "  make lint           Lint code with ruff"
	@echo "  make fix            Fix linting issues"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      Start all services with docker-compose"
	@echo "  make docker-down    Stop docker-compose services"
	@echo "  make docker-logs    Follow app logs"
	@echo "  make docker-build   Rebuild and start app container"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove cache and temp files"

# =============================================================================
# Setup & Installation
# =============================================================================

install:
	poetry install

# =============================================================================
# Development
# =============================================================================

dev:
	docker compose -f compose.yml up --build

run: dev

dev-app:
	poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	poetry run python worker.py

# =============================================================================
# Testing
# =============================================================================

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=app --cov-report=term-missing

test-cov-html:
	poetry run pytest --cov=app --cov-report=html

test-level1:
	poetry run pytest tests/test_level1_infrastructure.py -v

test-level2:
	poetry run pytest tests/test_level2_services.py -v

test-level3:
	poetry run pytest tests/test_level3_api.py -v

test-level4:
	poetry run pytest tests/test_level4_ui.py -v

# =============================================================================
# Code Quality
# =============================================================================

format:
	poetry run ruff format .

lint:
	poetry run ruff check .

fix:
	poetry run ruff check . --fix

# =============================================================================
# Docker
# =============================================================================

docker-up:
	docker compose -f compose.yml up -d

docker-down:
	docker compose -f compose.yml down

docker-logs:
	docker compose -f compose.yml logs -f app

docker-build:
	docker compose -f compose.yml up -d --build

# =============================================================================
# Cleanup
# =============================================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
