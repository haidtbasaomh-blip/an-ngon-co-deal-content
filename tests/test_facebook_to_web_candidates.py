"""Offline tests for Meta -> website staging: never publish or loop content back."""
import importlib.util
from pathlib import Path
import os
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fb_sync_staging", ROOT / "scripts" / "facebook_to_web_candidates.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FacebookCandidateTests(unittest.TestCase):
    def setUp(self):
        self.id = "123456789"
        self.site = "https://example-site.pages.dev"
        self.post = {
            "id": "123456789_9988",
            "from": {"id": self.id},
            "message": "Một bài hoàn toàn mới do Fanpage đăng, không phải dẫn từ website.",
            "permalink_url": "https://www.facebook.com/123456789/posts/9988",
            "is_published": True,
            "created_time": "2026-11-15T00:00:00+0000",
        }

    def test_accepts_new_owned_page_post_for_review_only(self):
        candidate = mod.normalize_page_post(self.post, self.id, self.site)
        self.assertIsNotNone(candidate)
        self.assertFalse(candidate["approved"])
        self.assertEqual(candidate["publicationStatus"], "draft_for_review")
        self.assertFalse(candidate["publishToFacebook"])
        self.assertTrue(candidate["neverRepublishToFacebook"])

    def test_rejects_wrong_page(self):
        self.assertIsNone(mod.normalize_page_post(self.post, "999", self.site))

    def test_rejects_web_origin_link_to_prevent_loop(self):
        p = dict(self.post)
        p["link"] = self.site + "/bai-viet/chu-de/"
        self.assertIsNone(mod.normalize_page_post(p, self.id, self.site))
        p = dict(self.post)
        p["message"] += " Xem chi tiết: " + self.site + "/cam-nang/foo/"
        self.assertIsNone(mod.normalize_page_post(p, self.id, self.site))

    def test_does_not_block_similar_but_unrelated_domains(self):
        p = dict(self.post)
        p["link"] = "https://not-" + self.site.split("://")[1] + "/news"
        self.assertIsNotNone(mod.normalize_page_post(p, self.id, self.site))

    def test_unpublished_and_short_content_rejected(self):
        p = dict(self.post); p["is_published"] = False
        self.assertIsNone(mod.normalize_page_post(p, self.id, self.site))
        p = dict(self.post); p["message"] = "hi"
        self.assertIsNone(mod.normalize_page_post(p, self.id, self.site))

    def test_rejects_site_urls_without_scheme_or_with_www(self):
        variants = [
            self.site.replace("https://", "") + "/bai-viet/nhap-tu-web/",
            "WWW." + self.site.replace("https://", "").upper() + "/bai-viet/x/",
            self.site.upper() + "/bai-viet/x/",
        ]
        for value in variants:
            with self.subTest(value=value):
                post = dict(self.post)
                post["message"] += " " + value
                self.assertIsNone(mod.normalize_page_post(post, self.id, self.site))

    def test_accepts_unrelated_similar_domains_without_false_loop(self):
        variants = [
            "https://not-example-site.pages.dev/bai-viet/x/",
            "https://example-site.pages.dev.evil.test/bai-viet/x/",
            "https://example-site.pages.dev-other.test/bai-viet/x/",
        ]
        for value in variants:
            with self.subTest(value=value):
                post = dict(self.post)
                post["link"] = value
                self.assertIsNotNone(mod.normalize_page_post(post, self.id, self.site))

    def test_duplicate_content_from_multiple_post_ids_stages_once(self):
        first = dict(self.post)
        duplicate = dict(self.post)
        duplicate["id"] = self.id + "_9989"
        duplicate["permalink_url"] = "https://www.facebook.com/" + self.id + "/posts/9989"
        items = mod.stage_candidates([first, duplicate, first], self.id, self.site)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["facebook_post_id"], first["id"])
        self.assertEqual(items[0]["idempotency_key"],
                         self.id + ":" + items[0]["normalized_content_hash"])
        self.assertFalse(items[0]["approved"])

    def test_dedupe_does_not_cross_page_identity(self):
        other = dict(self.post)
        other["from"] = {"id": "other"}
        self.assertEqual(len(mod.stage_candidates([other], self.id, self.site)), 0)

    def test_missing_credentials_fail_closed_without_network(self):
        with patch.dict(os.environ, {"META_PAGE_ACCESS_TOKEN": "", "META_PAGE_ID": "", "META_EXPECTED_PAGE_ID": ""}):
            self.assertEqual(mod.main(), 0)

if __name__ == "__main__":
    unittest.main()
