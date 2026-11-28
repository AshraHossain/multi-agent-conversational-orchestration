"""Thread-safe local JSON RunStore and storage protocol with path-traversal protection."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Protocol
from uuid import UUID

from .models import RunRecord, Status


class RunStoreProtocol(Protocol):
    """Storage interface implemented by local JSON RunStore and MongoRunStore."""

    def save(self, record: RunRecord) -> None: ...

    def get(self, run_id: str) -> RunRecord | None: ...

    def list_runs(
        self,
        *,
        status: Status | None = None,
        incident_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RunRecord], int]: ...

    def get_idempotency(self, key: str) -> tuple[str, str] | None: ...

    def set_idempotency(self, key: str, payload_hash: str, run_id: str) -> None: ...

    def is_ready(self) -> bool: ...


class RunStore:
    """Small local dev store. Use durable DB + transactions for production."""

    def __init__(self, directory: str = "artifacts/runs"):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        self._idempotency: dict[str, tuple[str, str]] = {}

    def _safe_path(self, run_id: str) -> Path:
        normalized = str(UUID(run_id))
        target = (self.directory / f"{normalized}.json").resolve()
        if target.parent != self.directory:
            raise ValueError("Invalid run ID path")
        return target

    def is_ready(self) -> bool:
        return self.directory.exists() and self.directory.is_dir()

    def get_idempotency(self, key: str) -> tuple[str, str] | None:
        with self.lock:
            return self._idempotency.get(key)

    def set_idempotency(self, key: str, payload_hash: str, run_id: str) -> None:
        with self.lock:
            self._idempotency[key] = (payload_hash, run_id)

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

    def list_runs(
        self,
        *,
        status: Status | None = None,
        incident_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RunRecord], int]:
        with self.lock:
            if not self.directory.exists():
                return [], 0
            records: list[RunRecord] = []
            for path in self.directory.glob("*.json"):
                try:
                    rec = RunRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
                except (ValueError, OSError):
                    continue
                if status is not None and rec.status != status:
                    continue
                if incident_id is not None and rec.incident.incident_id != incident_id:
                    continue
                records.append(rec)

            records.sort(key=lambda r: r.created_at, reverse=True)
            total = len(records)
            return records[offset : offset + limit], total
