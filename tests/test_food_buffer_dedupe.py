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
        self.sent_posts = []
        self.bad_pagination = False
        self.create_calls = 0
        self.feed = fixture()
        self.page_mode = "ok"
        self.page_reads = 0
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
        if req.full_url == bridge.FEED:
            return io.BytesIO(self.feed)
        self.assertEqual(req.full_url, URL, "Unexpected page fetch or cross-site request")
        self.page_reads += 1
        if self.page_mode == "http404":
            raise bridge.urllib.error.HTTPError(req.full_url, 404, "Not found", {}, None)
        canonical = URL if self.page_mode != "wrong_canonical" else URL + "other/"
        robots = "noindex,nofollow" if self.page_mode == "noindex" else "index,follow"
        og = "" if self.page_mode == "missing_og" else '<meta property="og:title" content="Bai viet da duyet">'
        markup = (f'<html><head><link rel="canonical" href="{canonical}">'
                  f'<meta name="robots" content="{robots}">{og}</head><body>OK</body></html>')
        return io.BytesIO(markup.encode("utf-8"))

    def api(self, key, query, variables=None):
        self.assertEqual(key, "OFFLINE_TEST_ONLY")
        if "account { organizations" in query:
            return {"account": {"organizations": [{"id": "org-test"}]}}
        if "channels(input:" in query:
            return {"channels": [{"id": bridge.FOOD_CHANNEL_ID,
                                  "service": "facebook", "name": "Ăn Ngon Có Deal"}]}
        if "posts(first:" in query:
            if "status: [scheduled]" in query:
                return {"posts": {"edges": [{"node": p} for p in self.posts],
                                  "pageInfo": {"hasNextPage": False, "endCursor": None}}}
            if "status: [sent]" in query:
                second = 'after: "sent-page-2"' in query
                items = self.sent_posts[100:] if second else self.sent_posts[:100]
                more = not second and len(self.sent_posts) > 100
                cursor = "sent-page-2" if more else None
                if self.bad_pagination:
                    more, cursor = True, None
                return {"posts": {"edges": [{"node": p} for p in items],
                                  "pageInfo": {"hasNextPage": more, "endCursor": cursor}}}
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

    def test_public_page_is_checked_before_first_buffer_post(self):
        bridge.main()
        self.assertEqual(self.page_reads, 1)
        self.assertEqual(self.create_calls, 1)

    def test_noindex_or_wrong_canonical_or_missing_og_fails_closed(self):
        for mode in ("noindex", "wrong_canonical", "missing_og"):
            with self.subTest(mode=mode):
                self.page_mode = mode
                with self.assertRaisesRegex(RuntimeError, "canonical/indexable OG"):
                    bridge.main()
                self.assertEqual(self.create_calls, 0)
                self.assertFalse(self.path.exists())

    def test_live_article_http_404_does_not_queue(self):
        self.page_mode = "http404"
        with self.assertRaises(bridge.urllib.error.HTTPError):
            bridge.main()
        self.assertEqual(self.create_calls, 0)

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

    def test_sent_post_on_second_buffer_page_is_not_reposted(self):
        # Buffer limits reads to 100 posts/page. A link at position 101 must be detected.
        self.sent_posts = [{"id": "old-" + str(i), "text": "Unrelated old post"}
                           for i in range(100)]
        self.sent_posts.append({"id": "old-101", "text": "Previously sent: " + URL})
        bridge.main()
        self.assertEqual(self.create_calls, 0, "A previously sent article was queued again")
        self.assertEqual(json.loads(self.path.read_text())["queued_urls"], [URL])

    def test_missing_buffer_cursor_fails_closed_before_posting(self):
        self.bad_pagination = True
        self.sent_posts = [{"id": "old", "text": "Unrelated"}]
        with self.assertRaisesRegex(RuntimeError, "cursor"):
            bridge.main()
        self.assertEqual(self.create_calls, 0)

    def test_buffer_queue_near_free_limit_does_not_overfill(self):
        self.posts = [{"id": "pending-" + str(i), "text": "Another queued post"}
                      for i in range(9)]
        bridge.main()
        self.assertEqual(self.create_calls, 0)

class FeedParsingTest(unittest.TestCase):
    def test_reasons_account_for_every_feed_item(self):
        good = fixture().decode("utf-8").split("<item>",1)[1].split("</item>",1)[0]
        def item(slug, date, title=None, desc=None):
            u = bridge.SITE + "/bai-viet/" + slug
            return ("<item><title>" + (title or "Bai viet am thuc duoc kiem tra") +
                    "</title><link>" + u + "</link><description>" +
                    (desc or "Noi dung am thuc thuc te duoc kiem tra ky.") +
                    "</description><pubDate>" + date + "</pubDate></item>")
        date = "Tue, 17 Nov 2026 14:00:00 GMT"
        xml = ("<rss><channel><item>" + good + "</item>"
               + "<item>" + good + "</item>"
               + item("bad-date/", "not a timestamp")
               + item("missing-date/", "")
               + item("timezone-missing/", "Tue, 17 Nov 2026 14:00:00")
               + item("future/", "Fri, 17 Nov 2099 14:00:00 GMT")
               + item("wrong-path", date)
               + item("query/?p=1", date)
               + item("short-title/", date, title="ABC")
               + item("short-desc/", date, desc="ABC")
               + item("valid-second/", date) + "</channel></rss>")
        audit = {}
        found = bridge.read_feed(xml.encode(), audit, dt.datetime(2026,11,24,tzinfo=dt.timezone.utc))
        self.assertEqual(len(found), 2)
        self.assertEqual(audit["rssItems"], 11)
        self.assertEqual(audit["parsedEligibleArticles"], 2)
        self.assertEqual(audit["excludedCounts"], {
            "duplicate_url": 1, "invalid_pubdate": 1, "missing_pubdate": 1,
            "timezone_missing": 1, "future_pubdate": 1,
            "noncanonical_article_url": 2, "title_too_short": 1, "description_too_short": 1
        })
        self.assertEqual(sum(audit["excludedCounts"].values()), 9)

    def test_invalid_date_does_not_block_valid_new_article(self):
        xml = fixture("not-a-date").decode().replace(URL, bridge.SITE + "/bai-viet/bad-date/")
        xml = xml.replace("</channel>", fixture().decode().split("<channel>")[1].split("</channel>")[0] + "</channel>")
        found = bridge.read_feed(xml.encode(), now=dt.datetime(2026,11,24,tzinfo=dt.timezone.utc))
        self.assertEqual([a["url"] for a in found], [URL])

if __name__ == "__main__":
    unittest.main()
