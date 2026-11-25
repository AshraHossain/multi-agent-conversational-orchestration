"""Structural, AST layering, immutability, ground-truth, and tool-allowlist invariant tests."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest
from pydantic import BaseModel

from ma_co import contracts
from ma_co.contracts import IncidentInput, Policy
from ma_co.core.reflection import FixtureJudge, FixtureRegenerator, ReflectionEngine
from ma_co.core.store import RunStore

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FORBIDDEN_FRAMEWORK_IMPORTS = frozenset(
    {
        "fastapi",
        "starlette",
        "uvicorn",
        "crewai",
        "langgraph",
        "google",
        "pymongo",
        "httpx",
    }
)


def _collect_imports(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
            imported.add(node.module.split(".")[0])
    return imported


@pytest.mark.unit
def test_core_and_contracts_never_import_frameworks() -> None:
    """AST guard: contracts/ and core/ must remain 100% framework- and SDK-free."""
    for layer in ("contracts", "core"):
        layer_dir = _REPO_ROOT / "src" / "ma_co" / layer
        py_files = sorted(layer_dir.rglob("*.py"))
        assert py_files, f"Expected Python modules in {layer_dir}"
        for py_file in py_files:
            imports = _collect_imports(py_file)
            forbidden = imports & _FORBIDDEN_FRAMEWORK_IMPORTS
            assert not forbidden, f"{py_file.name} imports forbidden frameworks: {forbidden}"

            if layer == "contracts":
                internal_leaks = {
                    m
                    for m in imports
                    if m.startswith(("ma_co.core", "ma_co.adapters", "ma_co.api"))
                }
                assert not internal_leaks, f"{py_file.name} leaks outer layers: {internal_leaks}"


@pytest.mark.unit
def test_all_contract_models_are_frozen() -> None:
    """Every Pydantic model exported by ma_co.contracts must be immutable."""
    models = [
        obj
        for _, obj in inspect.getmembers(contracts, inspect.isclass)
        if issubclass(obj, BaseModel) and obj is not BaseModel
    ]
    assert len(models) >= 6
    for model_cls in models:
        assert model_cls.model_config.get("frozen") is True, (
            f"{model_cls.__name__} must set ConfigDict(frozen=True)"
        )


@pytest.mark.unit
def test_ground_truth_never_leaks_into_runs_or_drafts(tmp_path: Path) -> None:
    """Evaluation case labels (case_id / expected_status) never enter RunRecord or drafts."""
    from ma_co.eval import GOLDEN_CASES

    store = RunStore(str(tmp_path))
    engine = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), Policy())

    for case in GOLDEN_CASES:
        incident = IncidentInput(
            incident_id=case.incident_id,
            alert=case.alert,
            evidence=case.evidence,
            proposed_action=case.proposed_action,
        )
        record = engine.run(incident, f"Incident {incident.incident_id}: {incident.alert}")
        store.save(record)
        dumped = record.model_dump_json()
        assert case.case_id not in dumped
        assert "expected_status" not in dumped


@pytest.mark.unit
def test_cross_agent_tool_use_is_denied() -> None:
    """Policy forbids write tools and CrewAI Safety Reviewer receives zero tools."""
    policy = Policy(forbidden_tools=frozenset({"shell", "kubectl_write", "email_send"}))
    engine = ReflectionEngine(FixtureJudge(), FixtureRegenerator(), policy)
    incident = IncidentInput(
        incident_id="INC-TOOL-01",
        alert="5xx spike",
        evidence=("Prometheus 12%",),
    )

    for forbidden in policy.forbidden_tools:
        with pytest.raises(ValueError, match="Forbidden tool"):
            engine.run(incident, "draft", used_tools={forbidden})

    crewai_src = (_REPO_ROOT / "src" / "ma_co" / "adapters" / "crewai_incident.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(crewai_src)
    reviewer_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Agent"
        and any(
            kw.arg == "role"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value == "Safety Reviewer"
            for kw in node.keywords
        )
    ]
    assert len(reviewer_calls) == 1
    kw_map = {kw.arg: kw.value for kw in reviewer_calls[0].keywords}
    assert "tools" not in kw_map, "Safety Reviewer must never receive execution or lookup tools"
    assert isinstance(kw_map.get("allow_delegation"), ast.Constant)
    assert kw_map["allow_delegation"].value is False
