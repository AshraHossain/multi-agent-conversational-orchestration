.PHONY: setup dev lint format typecheck test eval check docker-build

setup:
	uv sync --group dev

dev:
	uv run uvicorn ma_co.api.main:app --reload

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src/ma_co

test:
	uv run pytest --cov=ma_co --cov-report=term-missing --cov-fail-under=80

eval:
	uv run python -m ma_co.eval --guardrails --verifier-matrix

check: lint typecheck test eval

docker-build:
	docker build -t ma-co:latest .
