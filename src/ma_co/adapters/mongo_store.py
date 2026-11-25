"""Optional MongoDB-backed RunStore. Requires pymongo and MONGO_URI env var."""

from __future__ import annotations

import os
from uuid import UUID

from ma_co.core.models import RunRecord
from ma_co.core.validation import sanitize_identifier


class MongoRunStore:
    """MongoDB-backed RunStore. Same interface as core.store.RunStore."""

    def __init__(
        self,
        uri: str | None = None,
        db_name: str = "ma_co",
        collection: str = "runs",
    ) -> None:
        import pymongo

        uri = uri or os.environ["MONGO_URI"]
        self._col = pymongo.MongoClient(uri)[db_name][collection]

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
        doc.pop("_id", None)
        return RunRecord.model_validate(doc)
