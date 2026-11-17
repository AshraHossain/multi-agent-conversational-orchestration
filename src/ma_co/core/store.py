"""Thread-safe local JSON RunStore with path-traversal protection."""

import json
from pathlib import Path
from threading import RLock
from uuid import UUID

from .models import RunRecord


class RunStore:
    """Small local dev store. Use durable DB + transactions for production."""

    def __init__(self, directory: str = "artifacts/runs"):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()

    def _safe_path(self, run_id: str) -> Path:
        normalized = str(UUID(run_id))
        target = (self.directory / f"{normalized}.json").resolve()
        if target.parent != self.directory:
            raise ValueError("Invalid run ID path")
        return target

    def save(self, record: RunRecord) -> None:
        with self.lock:
            path = self._safe_path(record.run_id)
            staging = path.with_suffix(".tmp")
            staging.write_text(record.model_dump_json(indent=2), encoding="utf-8")
            staging.replace(path)

    def get(self, run_id: str) -> RunRecord | None:
        path = self._safe_path(run_id)
        with self.lock:
            if not path.exists():
                return None
            return RunRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
