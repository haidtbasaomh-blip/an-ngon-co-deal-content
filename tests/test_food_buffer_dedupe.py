"""BF-07: offline replay tests for the production Food RSS -> Buffer bridge.
All feed and Buffer API responses are mocked. Never performs network calls or posts.
"""
import datetime as dt
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "food_buffer_rss.py"
spec = importlib.util.spec_from_file_location("food_buffer_rss_under_test", SOURCE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

URL = "https://an-ngon-co-deal.bvthn-1903.chatgpt.site/bai-viet/test-after-cutover-20261117/"

def fixture(pub_date="Tue, 17 Nov 2026 14:00:00 GMT"):
    return ("""<?xml version="1.0"?>
<rss version="2.0"><channel><item>
<title>Bai viet am thuc moi da phe duyet</title>
<link>""" + URL + """</link>
<description>Thong tin am thuc thuc te, noi dung goc duoc kiem tra.</description>
<pubDate>""" + pub_date + """</pubDate>
</item></channel></rss>""").encode("utf-8")

class ReplayTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "buffer_food_seen.json"
        self.posts = []
        self.create_calls = 0
        self.feed = fixture()
        self.stack = [
            patch.object(bridge, "STATE", self.path),
            patch.object(bridge.urllib.request, "urlopen", side_effect=self.feed_response),
            patch.object(bridge, "graphql", side_effect=self.api),
            patch.dict(os.environ, {"FOOD_BUFFER_API_KEY": "OFFLINE_TEST_ONLY",
                                    "FOOD_BUFFER_CHANNEL_ID": bridge.FOOD_CHANNEL_ID,
                                    "FOOD_BUFFER_AUTO_QUEUE": "true"}),
        ]
        for patcher in self.stack:
            patcher.start()
            self.addCleanup(patcher.stop)

    def feed_response(self, req, timeout=20):
        self.assertEqual(req.full_url, bridge.FEED)
        return io.BytesIO(self.feed)

    def api(self, key, query, variables=None):
        self.assertEqual(key, "OFFLINE_TEST_ONLY")
        if "account { organizations" in query:
            return {"account": {"organizations": [{"id": "org-test"}]}}
        if "channels(input:" in query:
            return {"channels": [{"id": bridge.FOOD_CHANNEL_ID,
                                  "service": "facebook", "name": "Ăn Ngon Có Deal"}]}
        if "posts(first:" in query:
            if "status: [scheduled]" in query:
                return {"posts": {"edges": [{"node": p} for p in self.posts]}}
            if "status: [sent]" in query:
                return {"posts": {"edges": []}}
            self.fail("Unexpected Buffer post filter")
        if "createPost" in query:
            self.create_calls += 1
            item = {"id": "offline-test-post-1", "text": variables["input"]["text"]}
            self.posts.append(item)
            return {"createPost": {"post": item}}
        self.fail("Unexpected GraphQL query: " + query[:90])

    def test_replay_same_canonical_does_not_create_second_queue_post(self):
        bridge.main()
        self.assertEqual(self.create_calls, 1)
        self.assertEqual(json.loads(self.path.read_text())["queued_urls"], [URL])
        bridge.main()
        self.assertEqual(self.create_calls, 1, "Second run duplicated a post")
        self.assertEqual(len(self.posts), 1)

    def test_lost_ledger_still_dedupes_from_buffer_queue(self):
        bridge.main()
        self.assertEqual(self.create_calls, 1)
        self.path.unlink()
        bridge.main()
        self.assertEqual(self.create_calls, 1, "Missing ledger caused replay")
        self.assertEqual(json.loads(self.path.read_text())["queued_urls"], [URL])

    def test_old_article_is_not_backfilled_after_cutover(self):
        self.feed = fixture("Tue, 17 Nov 2026 13:00:00 GMT")
        bridge.main()
        self.assertEqual(self.create_calls, 0)
        self.assertEqual(json.loads(self.path.read_text())["queued_urls"], [])

    def test_wrong_channel_id_fails_closed(self):
        os.environ["FOOD_BUFFER_CHANNEL_ID"] = "INVALID-CHANNEL"
        with self.assertRaisesRegex(RuntimeError, "channel ID mismatch"):
            bridge.main()
        self.assertEqual(self.create_calls, 0)

if __name__ == "__main__":
    unittest.main()
