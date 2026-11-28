"""Pure deterministic validators, audit digests, secret redaction, and injection framing."""

import hashlib
import os
import re

from ma_co.core.models import IncidentInput, RunRecord

_UNSAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_CONTEXT_BOUNDARY_RE = re.compile(r"</?\s*untrusted_context\s*>", re.IGNORECASE)

_EVIDENCE_DENIAL_RE = re.compile(
    r"\b(?:no fixture evidence was available|no evidence was supplied|no evidence is available)\b",
    re.IGNORECASE,
)

_EXECUTION_CLAIM_RE = re.compile(
    r"(?<!\bno\s)(?<!\bnot\s)(?<!\bnever\s)"
    r"\b(?:"
    r"(?:i|we|agent|system)\s+(?:have\s+)?(?:executed|ran|performed|completed|triggered|applied)"
    r"\s+(?:the\s+)?(?:rollback|restart|remediation|hotfix|deployment|kubectl|scale)"
    r"|rolled\s+back\s+(?:the\s+)?(?:deployment|service|release|cluster|pod)"
    r"|restarted\s+(?:the\s+)?(?:pods?|service|deployment|container)"
    r"|executed\s+kubectl"
    r"|remediation\s+(?:has\s+been\s+)?executed"
    r"|deployed\s+(?:the\s+)?hotfix"
    r")\b",
    re.IGNORECASE,
)

_TOKEN_RE = re.compile(r"[A-Za-z0-9_%./:-]{2,}")
_STOPWORDS = frozenset(
    {"at", "in", "of", "to", "is", "on", "by", "or", "an", "as", "the", "and", "for", "utc"}
)

_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"), "Bearer [REDACTED_SECRET]"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"), "[REDACTED_SECRET]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "[REDACTED_SECRET]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b"), "[REDACTED_SECRET]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_SECRET]"),
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
)


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


def redact_secrets(text: str) -> str:
    """Deterministically redact common API tokens, keys, and emails from text."""
    redacted = text
    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def compute_audit_digest(record: RunRecord, previous_digest: str = "") -> str:
    """Compute a tamper-evident SHA-256 audit digest chained over key RunRecord fields."""
    payload = "|".join(
        [
            previous_digest,
            record.run_id,
            record.incident.incident_id,
            record.status.value,
            record.draft,
            str(record.approved_by or ""),
            str(record.reviewed_by or ""),
            str(record.review_decision or ""),
            record.review_note,
            str(record.parent_run_id or ""),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _evidence_tokens(evidence: tuple[str, ...]) -> set[str]:
    tokens: set[str] = set()
    for item in evidence:
        for match in _TOKEN_RE.findall(item.lower()):
            cleaned = match.strip(".,:;()[]")
            if len(cleaned) >= 2 and cleaned not in _STOPWORDS:
                tokens.add(cleaned)
    return tokens


def validate_incident_draft(incident: IncidentInput, draft: str) -> list[str]:
    """Return factual/structural/safety defects that must block the quality gate."""
    defects: list[str] = []

    declared_id = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?Incident ID:\s*([^\s]+)",
        draft,
    )
    if declared_id and declared_id.group(1).strip("`*") != incident.incident_id:
        defects.append(f"Declared incident ID does not match input {incident.incident_id}")
    elif incident.incident_id not in draft:
        defects.append(f"Input incident ID {incident.incident_id} is missing")

    if incident.evidence and _EVIDENCE_DENIAL_RE.search(draft):
        defects.append("Draft denies the existence of supplied evidence")

    if _EXECUTION_CLAIM_RE.search(draft):
        defects.append("Draft claims unauthorized remediation was executed (read-only invariant)")

    if incident.evidence and "Evidence:" in draft:
        ev_tokens = _evidence_tokens(incident.evidence)
        draft_lower = draft.lower()
        if ev_tokens and not any(tok in draft_lower for tok in ev_tokens):
            defects.append("Draft Evidence section does not ground to supplied evidence")

    return defects
