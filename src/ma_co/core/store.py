import json
from pathlib import Path
from threading import RLock
from uuid import UUID

from .models import RunRecord
from .validation import sanitize_identifier


class RunStore:
    """Small local dev store. Use durable DB + transactions for production."""

    def __init__(self, directory: str = "artifacts/runs") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()

    def _safe_path(self, run_id: str) -> Path:
        safe = sanitize_identifier(run_id)
        if safe != run_id:
            raise ValueError(f"Invalid run_id: {run_id!r}")
        return self.directory / f"{safe}.json"

    def save(self, record: RunRecord) -> None:
        path = self._safe_path(record.run_id)
        with self.lock:
            staging = path.with_suffix(".tmp")
            staging.write_text(record.model_dump_json(indent=2), encoding="utf-8")
            staging.replace(path)

    def get(self, run_id: str) -> RunRecord | None:
        UUID(run_id)  # raises ValueError for invalid UUIDs
        path = self._safe_path(run_id)
        with self.lock:
            if not path.exists():
                return None
            return RunRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
