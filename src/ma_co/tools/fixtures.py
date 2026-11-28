"""Read-only fixture telemetry. Live connectors belong behind scoped service credentials."""

from ma_co.tools.providers import (
    ALLOWED_SOURCES,
    FixtureTelemetryProvider,
    TelemetrySource,
)

_DEFAULT_PROVIDER = FixtureTelemetryProvider()


def lookup_event(
    incident_id: str,
    source: TelemetrySource,
) -> str:
    """Lookup a read-only fixture signal for an incident."""
    if source not in ALLOWED_SOURCES:
        raise ValueError(f"Unsupported source: {source!r}. Allowed: {sorted(ALLOWED_SOURCES)}")
    return _DEFAULT_PROVIDER.lookup(incident_id, source)
