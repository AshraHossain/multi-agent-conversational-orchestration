"""Offline 3-tier eval harness tests — no LLM calls, no network."""

import json
from pathlib import Path

import pytest

import ma_co.eval as ev


@pytest.mark.unit
def test_eval_module_importable() -> None:
    import ma_co.eval  # noqa: F401


@pytest.mark.unit
def test_eval_produces_report() -> None:
    report = ev.run_eval(n_runs=3)

    assert isinstance(report, dict)
    for key in ("recall_at_1", "grounding_rate", "guardrail_pass_rate"):
        assert key in report, f"Missing key: {key}"
        assert 0.0 <= report[key] <= 1.0

    for key in ("latency_p50_ms", "latency_p95_ms"):
        assert key in report, f"Missing key: {key}"
        assert report[key] >= 0


@pytest.mark.unit
def test_eval_writes_json(tmp_path: Path) -> None:
    target = tmp_path / "eval_report.json"
    ev.run_eval(n_runs=2, output_path=target)

    assert target.exists(), "eval_report.json not created"
    data = json.loads(target.read_text(encoding="utf-8"))
    assert "recall_at_1" in data


@pytest.mark.unit
def test_eval_scores_in_range(tmp_path: Path) -> None:
    report = ev.run_eval(n_runs=2, output_path=tmp_path / "eval.json")

    assert report["recall_at_1"] <= 1.0
    assert report["grounding_rate"] <= 1.0
    assert report["guardrail_pass_rate"] <= 1.0
    assert report["mean_final_score"] >= 0.0


@pytest.mark.integration
def test_eval_guardrails_verifier_matrix_and_repeat(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_file = tmp_path / "eval_3tier.json"
    exit_code = ev.main(
        ["--guardrails", "--verifier-matrix", "--repeat", "3", "--out", str(out_file)]
    )
    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Verifier Red-Team Matrix" in stdout

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["repeat"] == 3
    assert data["total_cases"] == len(ev.GOLDEN_CASES)
    assert data["total_cases"] == 20
    assert data["guardrails"]["total"] == 12
    assert data["guardrails"]["passed"] == 12
    assert data["guardrail_pass_rate"] == 1.0

    vm = data["verifier_matrix"]
    assert vm["detection_rate"] == 1.0
    assert vm["false_positives"] == 0
    assert "paraphrased_certainty" in vm["deterministic_blind_spots"]

    stats = data["repeat_stats"]
    assert stats["recall_at_1"]["mean"] == 1.0
    assert stats["recall_at_1"]["stdev"] == 0.0
    assert all(val == "3/3" for val in stats["per_case_compliance"].values())


@pytest.mark.unit
def test_eval_rejects_invalid_repeat() -> None:
    with pytest.raises(ValueError, match="repeat"):
        ev.run_eval(repeat=0)
