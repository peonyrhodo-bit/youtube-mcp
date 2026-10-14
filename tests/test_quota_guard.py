import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from server import YouTubeQuotaError, YouTubeQuotaGuard


class YouTubeQuotaGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "quota.sqlite3")
        self.env = patch.dict(os.environ, {
            "YOUTUBE_SEARCH_DAILY_LIMIT": "1",
            "YOUTUBE_OTHER_DAILY_QUOTA_UNITS": "2",
        })
        self.env.start()
        self.guard = YouTubeQuotaGuard(self.path)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_search_exhaustion_does_not_block_videos_list(self):
        event_id = self.guard.authorize("search", {"q": "first"})
        self.guard.finish(event_id, "error", "simulated failure")
        with self.assertRaises(YouTubeQuotaError):
            self.guard.authorize("search", {"q": "second"})
        other_event = self.guard.authorize("videos", {"id": "known-video"})
        self.guard.finish(other_event, "succeeded")
        self.assertTrue(other_event > event_id)

    def test_attempt_is_charged_before_request_and_failure_is_recorded(self):
        event_id = self.guard.authorize("videos", {"id": "known-video"})
        conn = self.guard._connect()
        try:
            row = conn.execute(
                "SELECT other_units FROM youtube_quota_usage WHERE created_at IS NOT NULL"
            ).fetchone()
            self.assertEqual(int(row["other_units"]), 1)
        finally:
            conn.close()
        self.guard.finish(event_id, "error", "timeout")
        conn = self.guard._connect()
        try:
            row = conn.execute(
                "SELECT status, reason FROM youtube_quota_events WHERE id = ?",
                (event_id,),
            ).fetchone()
            self.assertEqual(row["status"], "error")
            self.assertEqual(row["reason"], "timeout")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
