#!/usr/bin/env python3
"""Stage owned Facebook Page posts for website review. READ ONLY on Meta; NEVER writes to a website.

This connector does not publish to any website, Facebook, Buffer or Metricool.
It requires independently authorized Page credentials supplied only via secrets.
Do not commit its generated candidate file or supply tokens in chat.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "social_publishing_policy.json"
OUTPUT = ROOT / "out" / "facebook_to_web_candidates_LOCAL.json"
FB_GRAPH = "https://graph.facebook.com/v27.0"
ALLOWED_DOMAINS = {"facebook.com", "www.facebook.com", "m.facebook.com"}

def is_site_url(value: str, site: str) -> bool:
    """Only the configured website is treated as a loop-back origin."""
    value = str(value or "")
    host = urllib.parse.urlsplit(site).hostname
    for match in re.finditer(r"https?://[^\s<>\"']+", value, flags=re.I):
        url = match.group(0).rstrip(".,;:!?)")
        parts = urllib.parse.urlsplit(url)
        if parts.hostname == host:
            return True
    return False

def normalize_page_post(post: dict, page_id: str, site: str) -> dict | None:
    """Filter to new, owned Page posts not already sourced from this website."""
    if not isinstance(post, dict):
        return None
    from_id = str((post.get("from") or {}).get("id") or "")
    post_id = str(post.get("id") or "")
    if from_id != page_id or not post_id.startswith(page_id + "_"):
        return None
    if post.get("is_published") is False:
        return None
    message = re.sub(r"\s+", " ", str(post.get("message") or "")).strip()
    if len(message) < 30:
        return None
    link = str(post.get("link") or "")
    if is_site_url(message, site) or is_site_url(link, site):
        return None  # This was a website -> Facebook post; never loop it back.
    permalink = str(post.get("permalink_url") or "")
    parsed = urllib.parse.urlsplit(permalink)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOMAINS:
        return None
    fingerprint = hashlib.sha256((page_id + "|" + message.casefold()).encode("utf-8")).hexdigest()
    return {
        "source": "own_facebook_page",
        "facebook_page_id": page_id,
        "facebook_post_id": post_id,
        "permalink_url": permalink,
        "created_time": str(post.get("created_time") or ""),
        "text": message,
        "normalized_content_hash": fingerprint,
        "approved": False,
        "publicationStatus": "draft_for_review",
        "publishToFacebook": False,
        "neverRepublishToFacebook": True,
    }

def fetch_json(path: str, token: str, params: dict | None = None) -> dict:
    query = urllib.parse.urlencode(params or {})
    uri = FB_GRAPH + path + (("?" + query) if query else "")
    req = urllib.request.Request(uri, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "WebFacebookReverseStaging/1.0",
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    site = str(policy.get("website") or "").rstrip("/")
    if policy.get("project") not in {"pc-gia-tot", "an-ngon-co-deal"} or not site.startswith("https://"):
        raise RuntimeError("Invalid target website policy. Stopped before reading Facebook.")
    token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
    page_id = os.getenv("META_PAGE_ID", "").strip()
    expected = os.getenv("META_EXPECTED_PAGE_ID", "").strip()
    if not token or not page_id or not expected:
        print("SAFE HOLD: Page token and verified Page ID have not been configured.")
        return 0
    if not page_id.isdecimal() or page_id != expected:
        raise RuntimeError("Page ID mismatch. No posts read or imported.")
    identity = fetch_json("/" + page_id, token, {"fields": "id,name"})
    if str(identity.get("id")) != expected:
        raise RuntimeError("Meta Page identity differs from expected Page ID")
    response = fetch_json("/" + page_id + "/feed", token, {
        "fields": "id,from{id},message,link,permalink_url,is_published,created_time",
        "limit": 25,
    })
    items, seen = [], set()
    for post in response.get("data") or []:
        candidate = normalize_page_post(post, expected, site)
        if candidate and candidate["facebook_post_id"] not in seen:
            seen.add(candidate["facebook_post_id"])
            items.append(candidate)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "schema": 1,
        "targetProject": policy["project"],
        "targetSite": site,
        "sourcePage": expected,
        "autoPublish": False,
        "count": len(items),
        "candidates": items,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Read-only candidates prepared:", len(items))
    print("No website, Buffer, Metricool, Zapier or Facebook post was published.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
