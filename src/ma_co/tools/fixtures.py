"""Read-only fixture telemetry. Live connectors belong behind scoped service credentials."""

from typing import Literal

_ALLOWED_SOURCES: frozenset[str] = frozenset({"prometheus", "github", "kubernetes"})

_EVENTS: dict[str, dict[str, str]] = {
    "INC-001": {
        "prometheus": "5xx rate 12% at 10:05 UTC",
        "github": "deploy abc123 at 10:02 UTC",
        "kubernetes": "3/4 pods ready; no remediation executed",
    }
}


def lookup_event(
    incident_id: str,
    source: Literal["prometheus", "github", "kubernetes"],
) -> str:
    if source not in _ALLOWED_SOURCES:
        raise ValueError(f"Unsupported source: {source!r}. Allowed: {sorted(_ALLOWED_SOURCES)}")
    return _EVENTS.get(incident_id, {}).get(source, "No fixture evidence available")
