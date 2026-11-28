"""Observability re-exports backed by ma_co.telemetry."""

from ma_co.telemetry import MetricsRegistry, metrics, start_span, trace_span

__all__ = ["MetricsRegistry", "metrics", "start_span", "trace_span"]
