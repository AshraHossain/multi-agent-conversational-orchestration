"""Optional MongoDB-backed RunStore with indexing, filtering, and readiness checks."""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from ma_co.core.models import RunRecord, Status
from ma_co.core.validation import sanitize_identifier


class MongoRunStore:
    """MongoDB-backed RunStore conforming to RunStoreProtocol."""

    def __init__(
        self,
        uri: str | None = None,
        db_name: str = "ma_co",
        collection: str = "runs",
    ) -> None:
        import pymongo

        resolved_uri = (uri or os.environ.get("MONGO_URI", "")).strip()
        if not resolved_uri:
            raise RuntimeError("MONGO_URI is required for MongoRunStore")
        self._client: Any = pymongo.MongoClient(resolved_uri)
        self._db: Any = self._client[db_name]
        self._col: Any = self._db[collection]
        try:
            self._idem_col: Any = self._db[f"{collection}_idempotency"]
        except KeyError:
            self._idem_col = None
        self._idempotency_cache: dict[str, tuple[str, str]] = {}
        self._ensure_indexes()

    def get_idempotency(self, key: str) -> tuple[str, str] | None:
        if self._idem_col is not None:
            doc = self._idem_col.find_one({"_id": key})
            if doc is not None:
                return str(doc["payload_hash"]), str(doc["run_id"])
            return None
        return self._idempotency_cache.get(key)

    def set_idempotency(self, key: str, payload_hash: str, run_id: str) -> None:
        if self._idem_col is not None:
            self._idem_col.replace_one(
                {"_id": key},
                {"_id": key, "payload_hash": payload_hash, "run_id": run_id},
                upsert=True,
            )
            return
        self._idempotency_cache[key] = (payload_hash, run_id)

    def _ensure_indexes(self) -> None:
        create_index = getattr(self._col, "create_index", None)
        if callable(create_index):
            create_index([("created_at", -1)])
            create_index([("status", 1), ("created_at", -1)])
            create_index([("incident.incident_id", 1), ("created_at", -1)])

    def is_ready(self) -> bool:
        try:
            command = getattr(self._db, "command", None)
            if callable(command):
                command("ping")
            return True
        except Exception:
            return False

    def save(self, record: RunRecord) -> None:
        doc = record.model_dump(mode="json")
        doc["_id"] = record.run_id
        self._col.replace_one({"_id": record.run_id}, doc, upsert=True)

    def get(self, run_id: str) -> RunRecord | None:
        UUID(run_id)  # guard
        safe = sanitize_identifier(run_id)
        doc = self._col.find_one({"_id": safe})
        if doc is None:
            return None
        doc_copy = dict(doc)
        doc_copy.pop("_id", None)
        return RunRecord.model_validate(doc_copy)

    def list_runs(
        self,
        *,
        status: Status | None = None,
        incident_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RunRecord], int]:
        query: dict[str, Any] = {}
        if status is not None:
            query["status"] = status.value
        if incident_id is not None:
            query["incident.incident_id"] = incident_id

        total = int(self._col.count_documents(query))
        cursor = self._col.find(query).sort("created_at", -1).skip(offset).limit(limit)
        records: list[RunRecord] = []
        for raw_doc in cursor:
            doc_copy = dict(raw_doc)
            doc_copy.pop("_id", None)
            records.append(RunRecord.model_validate(doc_copy))
        return records, total
