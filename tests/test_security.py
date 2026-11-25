"""Security branch coverage: 401, 413, 415, 429, path traversal."""

import pytest
from fastapi.testclient import TestClient


def _make_client(token: str | None = None, rate_limit: int = 120):
    env = {}
    if token:
        env["API_AUTH_TOKEN"] = token
    env["RATE_LIMIT_PER_MINUTE"] = str(rate_limit)
    env["MAX_PAYLOAD_BYTES"] = str(256)

    with pytest.MonkeyPatch().context() as mp:
        for k, v in env.items():
            mp.setenv(k, v)
        # Re-import to pick up new env values
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        return TestClient(mod.app, raise_server_exceptions=False), mod.app


@pytest.mark.unit
def test_no_auth_token_allows_all():
    with pytest.MonkeyPatch().context() as mp:
        mp.delenv("API_AUTH_TOKEN", raising=False)
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        r = client.post(
            "/v1/incidents/triage",
            json={
                "incident_id": "S-001",
                "alert": "test",
                "evidence": [],
                "proposed_action": "none",
            },
        )
        assert r.status_code == 201


@pytest.mark.unit
def test_valid_token_passes():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("API_AUTH_TOKEN", "secret-token")
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        r = client.post(
            "/v1/incidents/triage",
            headers={"X-API-Key": "secret-token"},
            json={
                "incident_id": "S-002",
                "alert": "test",
                "evidence": [],
                "proposed_action": "none",
            },
        )
        assert r.status_code == 201


@pytest.mark.unit
def test_wrong_token_401():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("API_AUTH_TOKEN", "correct-token")
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        r = client.post(
            "/v1/incidents/triage",
            headers={"X-API-Key": "wrong-token"},
            json={"incident_id": "S-003", "alert": "x", "evidence": [], "proposed_action": "x"},
        )
        assert r.status_code == 401


@pytest.mark.unit
def test_missing_token_401():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("API_AUTH_TOKEN", "secret")
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        r = client.post(
            "/v1/incidents/triage",
            json={"incident_id": "S-004", "alert": "x", "evidence": [], "proposed_action": "x"},
        )
        assert r.status_code == 401


@pytest.mark.unit
def test_probe_bypasses_auth():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("API_AUTH_TOKEN", "secret")
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        for path in ("/health", "/healthz", "/readyz"):
            assert client.get(path).status_code == 200


@pytest.mark.unit
def test_wrong_content_type_415():
    with pytest.MonkeyPatch().context() as mp:
        mp.delenv("API_AUTH_TOKEN", raising=False)
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        r = client.post(
            "/v1/incidents/triage",
            content=b"not json",
            headers={"Content-Type": "text/plain"},
        )
        assert r.status_code == 415


@pytest.mark.unit
def test_oversized_payload_413():
    with pytest.MonkeyPatch().context() as mp:
        mp.delenv("API_AUTH_TOKEN", raising=False)
        mp.setenv("MAX_PAYLOAD_BYTES", "10")
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        r = client.post(
            "/v1/incidents/triage",
            json={
                "incident_id": "S-005",
                "alert": "x" * 200,
                "evidence": [],
                "proposed_action": "x",
            },
        )
        assert r.status_code == 413


@pytest.mark.unit
def test_rate_limit_429():
    with pytest.MonkeyPatch().context() as mp:
        mp.delenv("API_AUTH_TOKEN", raising=False)
        mp.setenv("RATE_LIMIT_PER_MINUTE", "2")
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        payload = {"incident_id": "S-RL", "alert": "x", "evidence": [], "proposed_action": "x"}
        # Exhaust the limit
        for _ in range(2):
            client.post("/v1/incidents/triage", json=payload)
        r = client.post("/v1/incidents/triage", json=payload)
        assert r.status_code == 429
        assert "Retry-After" in r.headers


@pytest.mark.unit
def test_path_traversal_in_run_id_400():
    with pytest.MonkeyPatch().context() as mp:
        mp.delenv("API_AUTH_TOKEN", raising=False)
        import importlib

        import ma_co.api.main as mod

        importlib.reload(mod)
        client = TestClient(mod.app, raise_server_exceptions=False)
        r = client.get("/v1/runs/../../etc/passwd")
        assert r.status_code in (400, 404)
