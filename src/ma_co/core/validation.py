"""Pure deterministic validators, identifier sanitizers, and injection framing."""

import os
import re

from ma_co.core.models import IncidentInput

_UNSAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_CONTEXT_BOUNDARY_RE = re.compile(r"</?\s*untrusted_context\s*>", re.IGNORECASE)


def sanitize_identifier(raw_id: str, max_length: int = 128) -> str:
    """Strip path traversal components and unsafe characters from an identifier."""
    base = os.path.basename(raw_id.strip())
    cleaned = _UNSAFE_ID_RE.sub("_", base).strip("._")
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("Invalid identifier")
    return cleaned[:max_length]


def frame_untrusted_text(text: str, tag: str = "untrusted_context") -> str:
    """Neutralize XML boundary-escape tags and wrap untrusted text as passive data."""
    safe_tag = sanitize_identifier(tag, max_length=40)
    neutralized = _CONTEXT_BOUNDARY_RE.sub("[redacted_boundary_tag]", text)
    return f"<{safe_tag}>\n{neutralized}\n</{safe_tag}>"


def validate_incident_draft(incident: IncidentInput, draft: str) -> list[str]:
    """Return factual/structural defects that must block the quality gate."""
    defects: list[str] = []

    declared_id = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?Incident ID:\s*([^\s]+)",
        draft,
    )
    if declared_id and declared_id.group(1).strip("`*") != incident.incident_id:
        defects.append(f"Declared incident ID does not match input {incident.incident_id}")
    elif incident.incident_id not in draft:
        defects.append(f"Input incident ID {incident.incident_id} is missing")

    if incident.evidence and re.search(
        r"\bno fixture evidence was available\b", draft, re.IGNORECASE
    ):
        defects.append("Draft denies the existence of supplied evidence")

    return defects
