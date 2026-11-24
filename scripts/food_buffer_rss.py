#!/usr/bin/env python3
"""Safe RSS -> Buffer queue for An Ngon Co Deal (never PC GIA TOT)."""
import html
from html.parser import HTMLParser
import datetime as dt
import email.utils
import json
import os
import re
import sys
import unicodedata
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

SITE = "https://an-ngon-co-deal.bvthn-1903.chatgpt.site"
FEED = SITE + "/rss.xml"
BUFFER = "https://api.buffer.com"
FOOD_CHANNEL_ID = "6af914e962b70b94b0375e37"  # Verified from logged-in Buffer Food channel settings
STATE = Path(__file__).resolve().parents[1] / "data" / "buffer_food_seen.json"


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.casefold())
                   if not unicodedata.combining(c))


def read_feed(data, diagnostics=None, now=None):
    """Keep the existing publication gate; explain each excluded RSS item.
    A single malformed publication date must not abort the entire feed.
    """
    articles, seen = [], set()
    items = ET.fromstring(data).findall("./channel/item")
    now = now or dt.datetime.now(dt.timezone.utc)
    excluded = {}
    rejected = []
    def reject(reason, url):
        excluded[reason] = excluded.get(reason, 0) + 1
        # Report only a simple public article slug, never arbitrary external URLs.
        match = re.fullmatch(re.escape(SITE) + r"/bai-viet/([a-z0-9-]+)/?", url)
        rejected.append({"reason": reason, "slug": match.group(1) if match else None})
    for node in items:
        url = (node.findtext("link") or "").strip()
        title = " ".join(html.unescape(node.findtext("title") or "").split())
        abstract = re.sub("<[^>]*>", " ", node.findtext("description") or "")
        abstract = " ".join(html.unescape(abstract).split())
        if not re.fullmatch(re.escape(SITE) + r"/bai-viet/[a-z0-9-]+/", url):
            reject("noncanonical_article_url", url)
            continue
        if url in seen:
            reject("duplicate_url", url)
            continue
        if len(title) < 8:
            reject("title_too_short", url)
            continue
        if len(abstract) < 15:
            reject("description_too_short", url)
            continue
        raw_date = node.findtext("pubDate") or ""
        if not raw_date.strip():
            reject("missing_pubdate", url)
            continue
        try:
            published = email.utils.parsedate_to_datetime(raw_date)
            if published is None or published.tzinfo is None:
                reject("timezone_missing", url)
                continue
            published = published.astimezone(dt.timezone.utc)
        except (TypeError, ValueError, OverflowError):
            reject("invalid_pubdate", url)
            continue
        if published > now:
            reject("future_pubdate", url)
            continue
        articles.append({"url": url, "title": title, "summary": abstract[:330],
                         "published": published})
        seen.add(url)
    if diagnostics is not None:
        diagnostics.update({"rssItems": len(items), "parsedEligibleArticles": len(articles),
                            "excludedCounts": excluded, "excludedArticles": rejected})
        assert len(items) == len(articles) + sum(excluded.values())
    return articles

def graphql(key, query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        BUFFER, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            output = json.load(res)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise RuntimeError("Buffer API rejected FOOD_BUFFER_API_KEY (401 Unauthorized). Check that GitHub secret stores the full active key, not a masked value, label, or 'Bearer ' prefix.") from None
        raise RuntimeError("Buffer API HTTP error " + str(exc.code) + "; no posts created.") from None
    if output.get("errors"):
        raise RuntimeError("Buffer GraphQL: " + str(output["errors"][0].get("message")))
    return output.get("data") or {}


def ensure_channel(key, channel_id):
    # Official Buffer API flow: account -> organization -> channels.
    account = graphql(key, "query { account { organizations { id } } }").get("account") or {}
    orgs = account.get("organizations") or []
    if len(orgs) != 1:
        raise RuntimeError("Could not verify exactly one Buffer organization. No posts sent.")
    org_id = json.dumps(str(orgs[0]["id"]))
    q = "query { channels(input: { organizationId: " + org_id + " }) { id name service } }"
    channels = graphql(key, q).get("channels") or []
    ch = next((item for item in channels if str(item.get("id")) == channel_id), None)
    if not ch:
        raise RuntimeError("Food Buffer channel ID not found in authenticated organization. No posts sent.")
    if str(ch.get("service") or "").lower() != "facebook":
        raise RuntimeError("Wrong channel type. No posts sent.")
    if "an ngon co deal" not in fold(str(ch.get("name") or "")):
        raise RuntimeError("Wrong Fanpage! Must be An Ngon Co Deal. No posts sent.")
    print("Verified Buffer Facebook food channel by exact ID, service and name.")


def recent_posts(key, channel_id, status):
    """Read paginated Buffer history; fail closed if dedupe cannot inspect it safely.

    Buffer caps a response at 100 items. Looking only at page one risks replaying
    an older Facebook post when the local GitHub ledger is lost or stale.
    """
    organizations = graphql(key, "query { account { organizations { id } } }")
    orgs = (organizations.get("account") or {}).get("organizations") or []
    if len(orgs) != 1:
        raise RuntimeError("Multiple Buffer organizations; cannot select safely.")
    org = json.dumps(str(orgs[0]["id"]))
    channel = json.dumps(channel_id)
    posts = []
    after = None
    used_cursors = set()
    for _ in range(3):  # Hard cap: max 300 historical posts per status; never spin/overuse Free API.
        after_arg = ", after: " + json.dumps(after) if after else ""
        q = ("query { posts(first: 100" + after_arg
             + ", input: {organizationId: " + org
             + ", filter: {status: [" + status + "], channelIds: [" + channel
             + "]}}) { edges { node { id text } } pageInfo { hasNextPage endCursor } } }")
        response = (graphql(key, q).get("posts") or {})
        posts.extend(x["node"] for x in response.get("edges", []) if x.get("node"))
        page = response.get("pageInfo") or {}
        if not isinstance(page.get("hasNextPage"), bool):
            raise RuntimeError("Buffer pagination metadata missing; no posts created.")
        if not page["hasNextPage"]:
            return posts
        cursor = page.get("endCursor")
        if not isinstance(cursor, str) or not cursor or cursor in used_cursors:
            raise RuntimeError("Buffer pagination cursor is missing or repeated; no posts created.")
        used_cursors.add(cursor)
        after = cursor
    raise RuntimeError("Buffer history exceeds safe 300-post audit cap; no posts created.")



class PublicPageMeta(HTMLParser):
    """Only read metadata on a publicly published Food article; do not edit it."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonical = ""
        self.og_title = ""
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "link" and tag.lower() != "meta":
            return
        attr = dict((str(k).lower(), str(v or "")) for k, v in attrs)
        if tag.lower() == "link" and "canonical" in attr.get("rel", "").lower().split():
            self.canonical = attr.get("href", "").strip()
        elif tag.lower() == "meta":
            if attr.get("property", "").lower() == "og:title":
                self.og_title = attr.get("content", "").strip()
            if attr.get("name", "").lower() in ("robots", "googlebot"):
                self.noindex |= "noindex" in attr.get("content", "").lower()


def verify_public_article(url):
    """Fail closed before Buffer creation unless the actual HTML is indexable and canonical."""
    if not (url.startswith(SITE + "/bai-viet/") and url.endswith("/")):
        raise RuntimeError("Food URL is outside the approved public article area")
    req = urllib.request.Request(url, headers={"User-Agent": "FoodBufferBridge/1.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        headers = getattr(res, "headers", None)
        if headers and "noindex" in str(headers.get("X-Robots-Tag", "")).lower():
            raise RuntimeError("Live Food article is marked noindex in response headers")
        page = res.read(500000).decode("utf-8", errors="replace")
    meta = PublicPageMeta()
    meta.feed(page)
    if meta.noindex or meta.canonical != url or not meta.og_title:
        raise RuntimeError("Live Food article lacks matching canonical/indexable OG metadata")
    return True


def caption(article):
    return ("🍜 " + article["title"] + "\n\n"
            + article["summary"] + "\n\n"
            + "🔎 Xem bài đầy đủ: " + article["url"] + "\n\n"
            + "#AnNgonCoDeal #AmThucViet #MonNgon")


def report_queue_status(status, detail=""):
    """Write an observable GitHub Actions outcome without leaking credentials or post data.

    A green workflow means a safe audit completed; it does not imply that
    a new Buffer item was scheduled or that Facebook published anything.
    """
    allowed = {
        "hold_publisher", "hold_cutover", "hold_credentials",
        "hold_queue_full", "no_eligible_article", "queued_one"
    }
    if status not in allowed:
        raise ValueError("Unknown Food Buffer queue status")
    print("FOOD_BUFFER_QUEUE_RESULT=" + status)
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        row = (
            "\n### Food RSS → Buffer: result\n"
            "- Status: **" + status + "**\n"
            "- Facebook post verified as published: **NO** "
            "(Buffer enqueue alone is not publication evidence)\n"
        )
        if detail:
            row += "- Note: " + detail + "\n"
        with open(summary_path, "a", encoding="utf-8") as out:
            out.write(row)


def main():
    # Single-publisher safeguard: Zapier -> Buffer owns food Facebook publication.
    # This standalone GitHub path must never publish the same RSS article again.
    policy_file = Path(__file__).resolve().parents[1] / "config" / "social_publishing_policy.json"
    policy = json.loads(policy_file.read_text(encoding="utf-8"))
    if policy.get("project") != "an-ngon-co-deal":
        raise RuntimeError("Wrong social publishing policy; no posts sent.")
    if (policy.get("activePublisher") != "github-buffer-direct"
            or not policy.get("otherPublishers", {}).get("github_buffer_direct", {}).get("mayPublish", False)):
        print("SAFE HOLD: Food publisher policy does not authorize GitHub Buffer queue.")
        report_queue_status("hold_publisher", "Policy blocks direct publishing")
        return
    # Defense in depth: enable only after the Zapier RSS publisher is manually switched OFF.
    # Never backfill old public feed entries during cutover.
    cutover_raw = policy.get("githubBufferCutoverUtc")
    if not cutover_raw:
        print("SAFE HOLD: no verified Zapier-off cutover timestamp; no posting.")
        report_queue_status("hold_cutover", "No verified cutover date")
        return
    cutover = dt.datetime.fromisoformat(cutover_raw.replace("Z", "+00:00"))
    if cutover.tzinfo is None:
        raise RuntimeError("Cutover timestamp must be UTC and timezone-aware")

    req = urllib.request.Request(FEED, headers={"User-Agent": "FoodBufferBridge/1.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        raw = res.read(1600001)
    if len(raw) > 1600000:
        raise RuntimeError("RSS exceeds safe read limit; no posts created.")
    diagnostics = {}
    articles = read_feed(raw, diagnostics=diagnostics)
    diagnostics["publishedAfterCutover"] = sum(a["published"] > cutover for a in articles)
    diagnostics["atOrBeforeCutover"] = sum(a["published"] <= cutover for a in articles)
    print("FOOD_RSS_PARSE_AUDIT " + json.dumps(diagnostics, ensure_ascii=False), flush=True)
    print("Public approved RSS articles:", len(articles))
    key = os.getenv("FOOD_BUFFER_API_KEY", "").strip()
    channel = (os.getenv("FOOD_BUFFER_CHANNEL_ID") or FOOD_CHANNEL_ID).strip()
    if channel != FOOD_CHANNEL_ID:
        raise RuntimeError("Food Buffer channel ID mismatch; no posts sent.")
    enabled = os.getenv("FOOD_BUFFER_AUTO_QUEUE", "").lower() == "true"
    if not (key and channel and enabled):
        print("SAFE MODE: missing credentials or enable flag; no Buffer posts created.")
        report_queue_status("hold_credentials", "Queue permission or configuration missing")
        return
    ensure_channel(key, channel)
    scheduled = recent_posts(key, channel, "scheduled")
    if len(scheduled) >= 9:
        print("Buffer queue has at least 9 posts; skipping.")
        report_queue_status("hold_queue_full", "Safe queue cap reached")
        return
    sent = recent_posts(key, channel, "sent")
    buffer_text = "\n".join(str(p.get("text") or "") for p in scheduled + sent)
    history = json.loads(STATE.read_text("utf-8")) if STATE.exists() else {}
    seen = set(history.get("queued_urls", []))
    queued_this_run = False
    for article in articles:  # RSS feed is newest-first; post only AFTER verified Zapier-off cutoff
        if article["published"] <= cutover:
            continue
        url = article["url"]
        if url in seen:
            continue
        if url in buffer_text:
            seen.add(url)
            continue
        verify_public_article(url)  # Live HTTP/canonical/OG/noindex gate before Facebook queueing.
        mutation = """mutation($input: CreatePostInput!) {
          createPost(input:$input) {
            ... on PostActionSuccess {post{id text dueAt}}
            ... on MutationError {message}
          }
        }"""
        result = graphql(key, mutation, {"input": {
            "text": caption(article), "channelId": channel,
            "schedulingType": "automatic", "mode": "addToQueue"
        }}).get("createPost") or {}
        if not (result.get("post") or {}).get("id"):
            raise RuntimeError("Buffer could not add to queue: " +
                               str(result.get("message") or "Unknown error"))
        print("One public food article added to Buffer queue.")
        queued_this_run = True
        seen.add(url)
        break  # MAXIMUM ONE NEW POST PER RUN
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(
        json.dumps({"schema": 1, "site": SITE, "queued_urls": sorted(seen)},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved anti-duplicate state. No secrets stored.")
    report_queue_status("queued_one" if queued_this_run else "no_eligible_article",
                        "One approved article queued; Facebook publication not yet verified" if queued_this_run
                        else "No new verified post-cutover article to enqueue")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Bridge safely stopped:", exc, file=sys.stderr)
        sys.exit(1)
