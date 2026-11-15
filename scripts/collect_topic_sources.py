#!/usr/bin/env python3
"""Collect public RSS HEADLINES and links for editorial research only.

Never copies article bodies or images. Never publishes to a website, Buffer,
Zapier, Metricool or Facebook. Uses only approved HTTPS feed URLs in config.
"""
from __future__ import annotations
import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "topic_sources.json"
OUTPUT = ROOT / "out" / "external_topic_ideas.json"
USER_AGENT = "ResearchTopicDiscovery/1.0 (reference headlines only)"
MAX_BYTES = 2_000_000
MAX_PER_FEED = 15
MAX_HISTORY = 150


def safe_link(raw, host):
    candidate = html.unescape((raw or "").strip())
    parts = urllib.parse.urlsplit(candidate)
    actual_host = (parts.hostname or "").lower()
    if (parts.scheme != "https"
            or not (actual_host == host or actual_host.endswith("." + host))
            or len(candidate) > 2048
            or not parts.path):
        return ""
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path,
                                    parts.query, ""))


def read_json(path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def collect_one(source):
    feed = source["rss_url"]
    host = source["allowed_article_host"].lower()
    p = urllib.parse.urlsplit(feed)
    if p.scheme != "https" or p.hostname not in [host, "www." + host]:
        raise ValueError("Feed/host mismatch: " + source["name"])
    req = urllib.request.Request(
        feed, headers={"User-Agent": USER_AGENT,
                       "Accept": "application/rss+xml, application/xml, text/xml"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("RSS larger than size limit")
    root = ET.fromstring(body)
    found = []
    for item in root.iter("item"):
        title = html.unescape((item.findtext("title") or "").strip())
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", title))[:250]
        link = safe_link(item.findtext("link"), host)
        if not title or not link:
            continue
        if any(x in title.lower() for x in ("[qc]", "[quảng cáo]", "[advertorial]")):
            continue
        found.append({
            "id": hashlib.sha256(link.encode("utf-8")).hexdigest()[:20],
            "source": source["name"],
            "sourceFeed": feed,
            "sourceUrl": link,
            "sourceTitle": title,
            "sourceDate": (item.findtext("pubDate") or "").strip()[:100],
            "editorialStatus": "idea_only",
            "approved": False,
            "publicationStatus": "not_published",
            "rights": "reference_only_no_republication",
        })
        if len(found) >= MAX_PER_FEED:
            break
    return found


def main():
    config = read_json(CONFIG, {})
    if config.get("schema") != 1 or config.get("purpose") != "reference_only":
        raise ValueError("Invalid read-only source config")
    previous = read_json(OUTPUT, {})
    retained = previous.get("ideas", []) if previous.get("schema") == 1 else []
    fresh, passed, failures = [], 0, []
    for source in config["feeds"]:
        try:
            ideas = collect_one(source)
            if not ideas:
                failures.append(source["name"] + ": no valid RSS items")
            else:
                fresh += ideas
                passed += 1
                print(source["name"] + ": " + str(len(ideas)) + " references")
        except Exception as exc:
            failures.append(source["name"] + ": " + type(exc).__name__)
    if not passed:
        print("No RSS source was reachable. Existing data left unchanged.", file=sys.stderr)
        print("; ".join(failures), file=sys.stderr)
        return 1
    uniq, seen = [], set()
    for item in fresh + retained:
        if item.get("id") in seen:
            continue
        seen.add(item["id"])
        uniq.append(item)
        if len(uniq) >= MAX_HISTORY:
            break
    output = {
        "schema": 1,
        "purpose": "editorial_research_not_for_publication",
        "autoPublish": False,
        "imagesCopied": False,
        "fullTextCopied": False,
        "count": len(uniq),
        "ideas": uniq,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print("Saved curated source headlines to " + str(OUTPUT))
    else:
        print("No new topic headlines")
    for err in failures:
        print("SKIP: " + err, file=sys.stderr)
    print("No website or Facebook publication performed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
