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
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "social_publishing_policy.json"
OUTPUT = ROOT / "out" / "facebook_to_web_candidates_LOCAL.json"
FB_GRAPH = "https://graph.facebook.com/v27.0"
ALLOWED_DOMAINS = {"facebook.com", "www.facebook.com", "m.facebook.com"}

def is_site_url(value: str, site: str) -> bool:
    """Find this site's URLs without treating subdomains of lookalikes as a match."""
    value = str(value or "")
    host = str(urllib.parse.urlsplit(site).hostname or "").lower().removeprefix("www.")
    if not host:
        return False
    full_url_pattern = r"https?://[^\s<>\"']+"
    # Parse qualified URLs first, then remove them before examining bare domains.
    # A lookalike such as site.example.evil.test must not be interpreted as a bare
    # mention of site.example.
    for match in re.finditer(full_url_pattern, value, flags=re.I):
        url = match.group(0).rstrip(".,;:!?)")
        parts = urllib.parse.urlsplit(url)
        url_host = str(parts.hostname or "").lower().removeprefix("www.")
        if url_host == host:
            return True
    without_urls = re.sub(full_url_pattern, " ", value, flags=re.I)
    bare = r"(?<![A-Za-z0-9_.-])(?:www\.)?" + re.escape(host) + r"(?=$|[/\s?#.,;:!)])"
    return re.search(bare, without_urls, flags=re.I) is not None

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
        "canonical_url": "https://www.facebook.com" + parsed.path.rstrip("/"),
        "created_time": str(post.get("created_time") or ""),
        "text": message,
        "normalized_content_hash": fingerprint,
        "idempotency_key": page_id + ":" + fingerprint,
        "approved": False,
        "publicationStatus": "draft_for_review",
        "publishToFacebook": False,
        "neverRepublishToFacebook": True,
    }

def stage_candidates(posts: list[dict], page_id: str, site: str) -> list[dict]:
    """Deduplicate by both Page post ID and normalized content, even across repost IDs."""
    items, post_ids, content_keys = [], set(), set()
    for post in posts:
        candidate = normalize_page_post(post, page_id, site)
        if not candidate:
            continue
        pid, content_key = candidate["facebook_post_id"], candidate["normalized_content_hash"]
        if pid in post_ids or content_key in content_keys:
            continue
        post_ids.add(pid)
        content_keys.add(content_key)
        items.append(candidate)
    return items

def canonical_facebook_url(url: str) -> str:
    """Stable canonical URL: omit tracking query/fragment, preserve post path."""
    p = urllib.parse.urlsplit(str(url or ""))
    if p.scheme != "https" or (p.hostname or "").lower() not in ALLOWED_DOMAINS:
        raise ValueError("Unexpected Facebook permalink origin")
    path = p.path.rstrip("/")
    if not path or path == "/":
        raise ValueError("Facebook post permalink path is missing")
    return "https://www.facebook.com" + path


def reconcile_snapshot(
    existing: dict | None,
    incoming: list[dict],
    project: str,
    page_id: str,
    site: str,
) -> dict:
    """Keep already staged candidates and reviewer notes; avoid duplicates on replay.

    This is staging-only and never approves, publishes or writes to a website.
    """
    if existing is None:
        saved = []
    else:
        if not isinstance(existing, dict) or existing.get("schema") not in (1, 2):
            raise RuntimeError("Unexpected existing Facebook staging schema")
        if (existing.get("targetProject") != project
                or existing.get("targetSite") != site
                or existing.get("sourcePage") != page_id
                or existing.get("autoPublish") is not False):
            raise RuntimeError("Existing staging belongs to another Page/site or is unsafe")
        saved = existing.get("candidates")
        if not isinstance(saved, list):
            raise RuntimeError("Existing staged candidates must be a list")

    result, seen_ids, seen_hashes, seen_canonicals = [], set(), set(), set()
    for row in [*saved, *incoming]:
        if not isinstance(row, dict):
            raise RuntimeError("Malformed staged candidate")
        if (row.get("facebook_page_id") != page_id
                or row.get("source") != "own_facebook_page"
                or row.get("publishToFacebook") is not False
                or row.get("neverRepublishToFacebook") is not True
                or row.get("idempotency_key") != page_id + ":" + str(row.get("normalized_content_hash") or "")):
            raise RuntimeError("Unsafe or cross-Page staged candidate; refusing overwrite")
        post_id = str(row.get("facebook_post_id") or "")
        digest = str(row.get("normalized_content_hash") or "")
        try:
            canonical = canonical_facebook_url(str(row.get("permalink_url") or ""))
        except ValueError as exc:
            raise RuntimeError("Untrusted staged Facebook permalink") from exc
        if not post_id.startswith(page_id + "_") or not digest:
            raise RuntimeError("Missing post identity or normalized hash")
        if post_id in seen_ids or digest in seen_hashes or canonical in seen_canonicals:
            continue
        seen_ids.add(post_id)
        seen_hashes.add(digest)
        seen_canonicals.add(canonical)
        result.append(row)  # Existing reviewer fields retain priority over replay.

    return {
        "schema": 2, "targetProject": project, "targetSite": site,
        "sourcePage": page_id, "autoPublish": False,
        "count": len(result), "candidates": result,
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
    items = stage_candidates(response.get("data") or [], expected, site)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else None
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError("Existing staging file is invalid; refusing to overwrite") from exc
    snapshot = reconcile_snapshot(existing, items, policy["project"], expected, site)
    # Atomic update: do not truncate a previously reviewed private candidate list.
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                         dir=OUTPUT.parent, prefix=OUTPUT.name + ".",
                                         suffix=".tmp", delete=False) as fp:
            temp_path = Path(fp.name)
            fp.write(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
        os.replace(temp_path, OUTPUT)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    print("Read-only new candidates:", len(items),
          "total candidates after idempotent merge:", snapshot["count"])
    print("No website, Buffer, Metricool, Zapier or Facebook post was published.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
