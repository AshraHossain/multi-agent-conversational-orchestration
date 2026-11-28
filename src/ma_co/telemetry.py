"""Lightweight Prometheus metrics registry and optional OpenTelemetry span helper."""

from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock
from typing import Any


class _NoOpSpan:
    """Zero-overhead fallback span used when opentelemetry is not installed."""

    def set_attribute(self, key: str, value: Any) -> None:
        return None


@contextmanager
def start_span(
    name: str,
    attributes: dict[str, str | int | float | bool] | None = None,
) -> Iterator[Any]:
    """Start an OpenTelemetry span when opentelemetry-api is installed, else no-op."""
    try:
        from opentelemetry import trace
    except ModuleNotFoundError:
        yield _NoOpSpan()
        return

    tracer: Any = trace.get_tracer(os.getenv("OTEL_SERVICE_NAME", "ma_co"))
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        yield span


trace_span = start_span


class MetricsRegistry:
    """Thread-safe Prometheus text exposition metrics registry."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._http_requests: dict[tuple[str, str, str], int] = defaultdict(int)
        self._triage_runs: dict[str, int] = defaultdict(int)
        self._reflection_iterations: int = 0
        self._vetoes_total: int = 0
        self._estimated_cost_usd: float = 0.0
        self._latency_ms_sum: float = 0.0
        self._latency_ms_count: int = 0

    def reset(self) -> None:
        with self._lock:
            self._http_requests.clear()
            self._triage_runs.clear()
            self._reflection_iterations = 0
            self._vetoes_total = 0
            self._estimated_cost_usd = 0.0
            self._latency_ms_sum = 0.0
            self._latency_ms_count = 0

    def record_http(self, method: str, status_code: int) -> None:
        self.record_request(method, "/", status_code, 0.0)

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        elapsed_ms: float,
    ) -> None:
        norm_path = path if path.count("/") <= 3 else "/v1/runs/{run_id}"
        with self._lock:
            self._http_requests[(method.upper(), norm_path, str(status_code))] += 1
            self._latency_ms_sum += max(0.0, elapsed_ms)
            self._latency_ms_count += 1

    def record_triage_run(
        self,
        status: str,
        iterations: int,
        estimated_cost_usd: float,
        veto_count: int = 0,
    ) -> None:
        with self._lock:
            self._triage_runs[status] += 1
            self._reflection_iterations += max(0, iterations)
            self._vetoes_total += max(0, veto_count)
            self._estimated_cost_usd += max(0.0, estimated_cost_usd)

    def record_run(
        self,
        status: str,
        estimated_cost_usd: float,
        veto_count: int = 0,
        iterations: int = 1,
    ) -> None:
        self.record_triage_run(status, iterations, estimated_cost_usd, veto_count)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "requests_total": sum(self._http_requests.values()),
                "runs_by_status": dict(self._triage_runs),
                "reflection_iterations_total": self._reflection_iterations,
                "vetoes_total": self._vetoes_total,
                "estimated_cost_usd_total": round(self._estimated_cost_usd, 6),
                "avg_request_latency_ms": round(
                    self._latency_ms_sum / max(1, self._latency_ms_count),
                    2,
                ),
            }

    def render_prometheus(self) -> str:
        with self._lock:
            lines: list[str] = [
                "# HELP ma_co_http_requests_total Total HTTP requests handled by ma_co.",
                "# TYPE ma_co_http_requests_total counter",
            ]
            for (method, path, code), count in sorted(self._http_requests.items()):
                lines.append(
                    f'ma_co_http_requests_total{{method="{method}",path="{path}",status="{code}"}} '
                    f"{count}"
                )

            lines.extend(
                [
                    "# HELP ma_co_triage_runs_total Total triage runs by terminal status.",
                    "# TYPE ma_co_triage_runs_total counter",
                ]
            )
            for st, count in sorted(self._triage_runs.items()):
                lines.append(f'ma_co_triage_runs_total{{status="{st}"}} {count}')

            lines.extend(
                [
                    "# HELP ma_co_reflection_iterations_total Total reflection iterations.",
                    "# TYPE ma_co_reflection_iterations_total counter",
                    f"ma_co_reflection_iterations_total {self._reflection_iterations}",
                    "# HELP ma_co_deterministic_vetoes_total Deterministic validation vetoes.",
                    "# TYPE ma_co_deterministic_vetoes_total counter",
                    f"ma_co_deterministic_vetoes_total {self._vetoes_total}",
                    "# HELP ma_co_estimated_cost_usd_total Cumulative estimated LLM cost (USD).",
                    "# TYPE ma_co_estimated_cost_usd_total counter",
                    f"ma_co_estimated_cost_usd_total {self._estimated_cost_usd:.6f}",
                    "# HELP ma_co_http_request_duration_ms_sum Cumulative HTTP latency (ms).",
                    "# TYPE ma_co_http_request_duration_ms_sum counter",
                    f"ma_co_http_request_duration_ms_sum {self._latency_ms_sum:.2f}",
                    "# HELP ma_co_http_request_duration_ms_count Timed HTTP request count.",
                    "# TYPE ma_co_http_request_duration_ms_count counter",
                    f"ma_co_http_request_duration_ms_count {self._latency_ms_count}",
                ]
            )
            return "\n".join(lines) + "\n"


metrics = MetricsRegistry()
