"""Pluggable read-only telemetry providers (offline fixtures + scoped HTTP GET)."""

from __future__ import annotations

import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Literal, Protocol

TelemetrySource = Literal["prometheus", "github", "kubernetes"]
ALLOWED_SOURCES: frozenset[str] = frozenset({"prometheus", "github", "kubernetes"})

_DEFAULT_FIXTURE_EVENTS: dict[str, dict[str, str]] = {
    "INC-001": {
        "prometheus": "5xx rate 12% at 10:05 UTC",
        "github": "deploy abc123 at 10:02 UTC",
        "kubernetes": "3/4 pods ready; no remediation executed",
    },
    "INC-104": {
        "prometheus": "active_conns=100/100 at 14:20 UTC",
        "github": "PR #482 pool-timeout config merged at 14:12 UTC",
        "kubernetes": "checkout-api CrashLoopBackOff (2 restarts); read-only snapshot",
    },
    "INC-105": {
        "prometheus": "dns_lookup_ms p95=410ms at 15:05 UTC",
        "github": "no recent dns-config deploys",
        "kubernetes": "coredns 2/2 pods healthy in ap-south-1",
    },
}


class TelemetryProvider(Protocol):
    """Strict read-only interface for querying incident telemetry signals."""

    def lookup(self, incident_id: str, source: TelemetrySource) -> str: ...


class FixtureTelemetryProvider:
    """Deterministic offline telemetry provider backed by immutable in-memory fixtures."""

    def __init__(self, events: dict[str, dict[str, str]] | None = None) -> None:
        self._events = events if events is not None else _DEFAULT_FIXTURE_EVENTS

    def lookup(self, incident_id: str, source: TelemetrySource) -> str:
        if source not in ALLOWED_SOURCES:
            raise ValueError(f"Unsupported source: {source!r}. Allowed: {sorted(ALLOWED_SOURCES)}")
        return self._events.get(incident_id, {}).get(source, "No fixture evidence available")


class HttpReadOnlyTelemetryProvider:
    """Opt-in read-only HTTP GET connector behind explicit per-source URL allowlists."""

    def __init__(
        self,
        endpoints: dict[str, str],
        *,
        timeout_seconds: float = 3.0,
        fallback: TelemetryProvider | None = None,
    ) -> None:
        validated: dict[str, str] = {}
        for src, url in endpoints.items():
            if src not in ALLOWED_SOURCES:
                raise ValueError(f"Unsupported source: {src!r}")
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in {"https", "http"} or not parsed.netloc:
                raise ValueError(f"Invalid telemetry endpoint URL for {src}: {url!r}")
            validated[src] = url.rstrip("/")
        self._endpoints = validated
        self._timeout = max(0.5, min(timeout_seconds, 15.0))
        self._fallback = fallback or FixtureTelemetryProvider()

    def lookup(self, incident_id: str, source: TelemetrySource) -> str:
        if source not in ALLOWED_SOURCES:
            raise ValueError(f"Unsupported source: {source!r}. Allowed: {sorted(ALLOWED_SOURCES)}")
        base_url = self._endpoints.get(source)
        if not base_url:
            return self._fallback.lookup(incident_id, source)

        quoted_id = urllib.parse.quote(incident_id, safe="")
        url = f"{base_url}?incident_id={quoted_id}"
        req = urllib.request.Request(url, method="GET", headers={"Accept": "text/plain"})  # noqa: S310
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                body = resp.read(2048).decode("utf-8", errors="replace").strip()
                return body or "No live telemetry returned"
        except (urllib.error.URLError, TimeoutError, OSError):
            return self._fallback.lookup(incident_id, source)


def get_telemetry_provider() -> TelemetryProvider:
    """Resolve the active read-only telemetry provider from environment configuration."""
    endpoints: dict[str, str] = {}
    env_map = {
        "prometheus": "PROMETHEUS_READONLY_URL",
        "github": "GITHUB_READONLY_URL",
        "kubernetes": "K8S_READONLY_URL",
    }
    for source, env_var in env_map.items():
        val = os.getenv(env_var, "").strip()
        if val:
            endpoints[source] = val
    if endpoints:
        return HttpReadOnlyTelemetryProvider(endpoints)
    return FixtureTelemetryProvider()
