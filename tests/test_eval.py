"""Offline eval harness tests — no LLM calls, no network."""
import json

import pytest

import ma_co.eval as ev


@pytest.mark.unit
def test_eval_module_importable():
    import ma_co.eval  # noqa: F401


@pytest.mark.unit
def test_eval_produces_report():
    report = ev.run_eval(n_runs=3)

    assert isinstance(report, dict)
    for key in ("recall_at_1", "grounding_rate", "guardrail_pass_rate"):
        assert key in report, f"Missing key: {key}"
        assert 0.0 <= report[key] <= 1.0

    for key in ("latency_p50_ms", "latency_p95_ms"):
        assert key in report, f"Missing key: {key}"
        assert report[key] >= 0


@pytest.mark.unit
def test_eval_writes_json():
    import pathlib

    ev.run_eval(n_runs=2)

    report_path = pathlib.Path("evaluation/eval_report.json")
    assert report_path.exists(), "eval_report.json not created"

    data = json.loads(report_path.read_text())
    assert "recall_at_1" in data


@pytest.mark.unit
def test_eval_scores_in_range():
    report = ev.run_eval(n_runs=2)

    assert report["recall_at_1"] <= 1.0
    assert report["grounding_rate"] <= 1.0
    assert report["guardrail_pass_rate"] <= 1.0
    assert report["mean_final_score"] >= 0.0
