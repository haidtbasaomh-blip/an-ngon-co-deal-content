"""Quality gates for the public staging feed."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_feed import SITE, check_article, clean_title

ROOT = Path(__file__).resolve().parents[1]


class TestEditorial(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "ready.json").read_text(encoding="utf-8"))

    def test_articles_unique_and_valid(self):
        self.assertEqual(self.data["site"], SITE)
        self.assertEqual(self.data["articleCount"], len(self.data["articles"]))
        keys = [check_article(a) for a in self.data["articles"]]
        self.assertEqual(len(keys), len(set(keys)))
        headings = [clean_title(a["title"]) for a in self.data["articles"]]
        self.assertEqual(len(headings), len(set(headings)))

    def test_no_affiliate_without_verified_tracking(self):
        self.assertTrue(all(not a.get("affiliateLinks") for a in self.data["articles"]))

    def test_no_publication_in_github_source(self):
        self.assertEqual("ready_for_site", self.data["status"])
        self.assertTrue(all(a["publicationStatus"] == "ready_for_site" for a in self.data["articles"]))

    def test_idempotent_offline_export(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            command = [sys.executable, str(ROOT / "scripts" / "prepare_feed.py"),
                       "--input", str(ROOT / "ready.json"), "--output", str(out),
                       "--offline"]
            subprocess.run(command, check=True, capture_output=True)
            first = {p.relative_to(out): p.read_bytes() for p in out.rglob("*.json")}
            subprocess.run(command, check=True, capture_output=True)
            second = {p.relative_to(out): p.read_bytes() for p in out.rglob("*.json")}
            self.assertEqual(first, second)
            self.assertEqual(37, json.loads((out / "manifest.json").read_text())["countReady"])


if __name__ == "__main__":
    unittest.main()
