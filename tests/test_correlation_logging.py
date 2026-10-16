import server


def test_video_stats_forwards_correlation_id(monkeypatch):
    seen = {}

    def fake_youtube_get(endpoint, params=None, correlation_id=None):
        seen["endpoint"] = endpoint
        seen["correlation_id"] = correlation_id
        return {"items": []}

    monkeypatch.setattr(server, "youtube_get", fake_youtube_get)
    server.get_video_stats(["video-id"], correlation_id="trace-123")
    assert seen["endpoint"] == "videos"
    assert seen["correlation_id"] == "trace-123"
