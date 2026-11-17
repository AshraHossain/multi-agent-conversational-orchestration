.PHONY: setup dev lint test eval check docker-build

setup:
	uv sync --group dev

dev:
	uv run uvicorn ma_co.api.main:app --reload

lint:
	uv run ruff check .

test:
	uv run pytest --cov=ma_co --cov-report=term-missing --cov-fail-under=80

eval:
	uv run python -m ma_co.eval

check: lint test eval

docker-build:
	docker build -t ma-co:latest .
