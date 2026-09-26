import json
from pathlib import Path
from threading import RLock

from .models import RunRecord


class RunStore:
    """Small local dev store. Use durable DB + transactions for production."""
    def __init__(self, directory: str = "artifacts/runs"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()

    def save(self, record: RunRecord) -> None:
        with self.lock:
            path = self.directory / f"{record.run_id}.json"
            staging = path.with_suffix(".tmp")
            staging.write_text(record.model_dump_json(indent=2), encoding="utf-8")
            staging.replace(path)

    def get(self, run_id: str) -> RunRecord | None:
        from uuid import UUID
        UUID(run_id)
        with self.lock:
            path = self.directory / f"{run_id}.json"
            if not path.exists():
                return None
            return RunRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
