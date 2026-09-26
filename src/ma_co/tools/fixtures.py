"""Read-only fixture inputs. Live tools belong behind scoped service credentials."""
EVENTS = {"INC-001": {"prometheus": "5xx rate 12% at 10:05 UTC",
                      "github": "deploy abc123 at 10:02 UTC",
                      "kubernetes": "3/4 pods ready; no remediation executed"}}


def lookup_event(incident_id: str, source: str) -> str:
    if source not in {"prometheus", "github", "kubernetes"}:
        raise ValueError("Unsupported source")
    return EVENTS.get(incident_id, {}).get(source, "No fixture evidence available")
