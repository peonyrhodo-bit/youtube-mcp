import os
import unittest
from unittest.mock import Mock, patch

from server import YouTubeQuotaError, YouTubeQuotaGuard


class YouTubeQuotaGuardTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "YOUTUBE_QUOTA_AUTH_URL": "https://director.example",
            "YOUTUBE_QUOTA_SHARED_SECRET": "test-secret",
        })
        self.env.start()
        self.guard = YouTubeQuotaGuard()

    def tearDown(self):
        self.env.stop()

    @patch("server.requests.post")
    def test_search_authorization_uses_central_authority(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {
            "allowed": True, "event_id": 42, "search_remaining": 0,
        })
        event_id = self.guard.authorize("search", {"q": "first"})
        self.assertEqual(event_id, 42)
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://director.example/internal/youtube-quota/authorize")
        self.assertEqual(kwargs["headers"]["X-Quota-Secret"], "test-secret")
        self.assertEqual(kwargs["json"]["bucket"], "search")
        self.assertEqual(kwargs["json"]["method"], "search.list")

    @patch("server.requests.post")
    def test_other_bucket_is_independent_and_finish_is_recorded(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"event_id": 43})
        event_id = self.guard.authorize("videos", {"id": "known-video"})
        self.guard.finish(event_id, "succeeded")
        self.assertEqual(post.call_count, 2)
        finish_payload = post.call_args.kwargs["json"]
        self.assertEqual(finish_payload, {
            "event_id": 43, "status": "succeeded", "reason": None,
        })

    def test_missing_authority_fails_closed(self):
        with patch.dict(os.environ, {
            "YOUTUBE_QUOTA_AUTH_URL": "",
            "YOUTUBE_QUOTA_SHARED_SECRET": "",
        }):
            guard = YouTubeQuotaGuard()
            with self.assertRaises(YouTubeQuotaError):
                guard.authorize("search", {"q": "blocked"})

    @patch("server.requests.post")
    def test_authority_outage_fails_closed_before_youtube_request(self, post):
        import requests
        post.side_effect = requests.Timeout("simulated")
        with self.assertRaises(YouTubeQuotaError):
            self.guard.authorize("search", {"q": "blocked"})

    @patch("server.requests.post")
    def test_exhausted_central_budget_is_rejected(self, post):
        post.return_value = Mock(status_code=429, json=lambda: {"detail": "budget_exhausted"})
        with self.assertRaises(YouTubeQuotaError):
            self.guard.authorize("search", {"q": "second"})


if __name__ == "__main__":
    unittest.main()
