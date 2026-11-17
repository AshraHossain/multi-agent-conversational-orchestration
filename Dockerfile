# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
COPY policies ./policies
COPY evaluation ./evaluation
RUN uv sync --frozen --no-dev

FROM python:3.11-slim-bookworm AS runtime

RUN groupadd --gid 10001 appgroup && \
    useradd --uid 10001 --gid appgroup --create-home --shell /sbin/nologin appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src
COPY --from=builder --chown=appuser:appgroup /app/policies /app/policies
COPY --from=builder --chown=appuser:appgroup /app/evaluation /app/evaluation

RUN mkdir -p /app/artifacts/runs && chown -R appuser:appgroup /app/artifacts

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "ma_co.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
