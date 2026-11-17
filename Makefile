.PHONY: setup lint test eval check dev docker-build

setup:
	uv sync --group dev --extra langgraph

lint:
	uv run ruff check .

test:
	uv run pytest --cov=ma_co --cov-report=term-missing --cov-fail-under=80

eval:
	uv run python -m ma_co.eval

check: lint test eval

dev:
	uv run uvicorn ma_co.api.main:app --reload

docker-build:
	docker build -t ma-co:latest .
