# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN uv sync --no-dev --extra langgraph --compile-bytecode

FROM python:3.11-slim AS runtime
RUN groupadd --gid 10001 appuser && useradd --uid 10001 --gid 10001 --no-create-home appuser
WORKDIR /app
COPY --from=builder /app /app
COPY policies/ policies/
COPY evaluation/ evaluation/
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "ma_co.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
