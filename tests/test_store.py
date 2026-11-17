import uuid

import pytest

from ma_co.core.models import IncidentInput, RunRecord
from ma_co.core.store import RunStore


def _store(tmp_path) -> RunStore:
    return RunStore(directory=str(tmp_path / "runs"))


def _record() -> RunRecord:
    incident = IncidentInput(
        incident_id="INC-ST01",
        alert="Disk full",
        evidence=("df -h: 100%",),
        proposed_action="cleanup",
    )
    return RunRecord(incident=incident, draft="Triage: disk full.")


@pytest.mark.unit
def test_save_and_get_roundtrip(tmp_path):
    store = _store(tmp_path)
    record = _record()
    store.save(record)
    loaded = store.get(record.run_id)
    assert loaded is not None
    assert loaded.run_id == record.run_id
    assert loaded.incident.incident_id == record.incident.incident_id


@pytest.mark.unit
def test_get_missing_returns_none(tmp_path):
    store = _store(tmp_path)
    assert store.get(str(uuid.uuid4())) is None


@pytest.mark.unit
def test_save_overwrites(tmp_path):
    from ma_co.core.models import Status, utc_now

    store = _store(tmp_path)
    record = _record()
    store.save(record)
    updated = record.model_copy(update={"status": Status.APPROVED_DRAFT, "updated_at": utc_now()})
    store.save(updated)
    loaded = store.get(record.run_id)
    assert loaded is not None
    assert loaded.status == Status.APPROVED_DRAFT


@pytest.mark.unit
def test_path_traversal_rejected(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store._safe_path("../etc/passwd")


@pytest.mark.unit
def test_invalid_uuid_rejected(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.get("not-a-uuid")


@pytest.mark.unit
def test_get_invalid_uuid_format(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.get("../../shadow")


@pytest.mark.unit
def test_atomic_write(tmp_path):
    """save() uses staging file so a crash mid-write can't leave a corrupt file."""
    store = _store(tmp_path)
    record = _record()
    store.save(record)
    # No .tmp file should remain after save
    tmp_files = list((tmp_path / "runs").glob("*.tmp"))
    assert tmp_files == []
