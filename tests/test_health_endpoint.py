import asyncio
import json
from types import SimpleNamespace

import server


def _payload(response):
    return json.loads(response.body.decode("utf-8"))


def test_health_reports_ready_configuration_without_live_api_request(monkeypatch):
    monkeypatch.setattr(server, "YOUTUBE_API_KEY", "configured-test-key")
    monkeypatch.setattr(server, "quota_guard", SimpleNamespace(
        auth_url="https://quota.example",
        shared_secret="test-secret",
    ))

    response = asyncio.run(server.health_check(None))
    payload = _payload(response)

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["checks"] == {
        "youtube_api_key_configured": True,
        "central_quota_authority_configured": True,
    }
    assert payload["youtube_api_live_probe"] == "not_performed_to_avoid_quota_consumption"


def test_health_reports_missing_upstream_configuration_as_degraded(monkeypatch):
    monkeypatch.setattr(server, "YOUTUBE_API_KEY", "")
    monkeypatch.setattr(server, "quota_guard", SimpleNamespace(
        auth_url="",
        shared_secret="",
    ))

    response = asyncio.run(server.health_check(None))
    payload = _payload(response)

    assert response.status_code == 200
    assert payload["status"] == "degraded"
    assert payload["checks"]["youtube_api_key_configured"] is False
    assert payload["checks"]["central_quota_authority_configured"] is False
