import re

from ma_co.core.models import IncidentInput


def validate_incident_draft(incident: IncidentInput, draft: str) -> list[str]:
    """Return factual/structural defects that must block the quality gate."""
    defects: list[str] = []

    declared_id = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?Incident ID:\s*([^\s]+)",
        draft,
    )
    if declared_id and declared_id.group(1).strip("`*") != incident.incident_id:
        defects.append(
            f"Declared incident ID does not match input {incident.incident_id}"
        )
    elif incident.incident_id not in draft:
        defects.append(f"Input incident ID {incident.incident_id} is missing")

    if incident.evidence and re.search(
        r"\bno fixture evidence was available\b", draft, re.IGNORECASE
    ):
        defects.append("Draft denies the existence of supplied evidence")

    return defects