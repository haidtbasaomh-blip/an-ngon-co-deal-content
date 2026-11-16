#!/usr/bin/env python3
"""Safe RSS -> Buffer queue for An Ngon Co Deal (never PC GIA TOT)."""
import html
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


def read_feed(data):
    articles, seen = [], set()
    for node in ET.fromstring(data).findall("./channel/item"):
        url = (node.findtext("link") or "").strip()
        title = " ".join(html.unescape(node.findtext("title") or "").split())
        abstract = re.sub("<[^>]*>", " ", node.findtext("description") or "")
        abstract = " ".join(html.unescape(abstract).split())
        if not (url.startswith(SITE + "/bai-viet/") and url.endswith("/")):
            continue
        if url in seen or len(title) < 8 or len(abstract) < 15:
            continue
        published = email.utils.parsedate_to_datetime(node.findtext("pubDate") or "") if node.findtext("pubDate") else None
        if published is None or published.tzinfo is None:
            continue  # Fail closed on missing/invalid publication timestamp
        articles.append({"url": url, "title": title, "summary": abstract[:330],
                         "published": published.astimezone(dt.timezone.utc)})
        seen.add(url)
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
    organizations = graphql(key, "query { account { organizations { id } } }")
    orgs = (organizations.get("account") or {}).get("organizations") or []
    if len(orgs) != 1:
        raise RuntimeError("Multiple Buffer organizations; cannot select safely.")
    org = json.dumps(str(orgs[0]["id"]))
    channel = json.dumps(channel_id)
    q = ("query { posts(first: 100, input: {organizationId: " + org
         + ", filter: {status: [" + status + "], channelIds: [" + channel
         + "]}}) { edges { node { id text } } } }")
    return [x["node"] for x in
            (graphql(key, q).get("posts") or {}).get("edges", [])
            if x.get("node")]


def caption(article):
    return ("🍜 " + article["title"] + "\n\n"
            + article["summary"] + "\n\n"
            + "🔎 Xem bài đầy đủ: " + article["url"] + "\n\n"
            + "#AnNgonCoDeal #AmThucViet #MonNgon")


def main():
    # Single-publisher safeguard: Zapier -> Buffer owns food Facebook publication.
    # This standalone GitHub path must never publish the same RSS article again.
    policy_file = Path(__file__).resolve().parents[1] / "config" / "social_publishing_policy.json"
    policy = json.loads(policy_file.read_text(encoding="utf-8"))
    if policy.get("project") != "an-ngon-co-deal":
        raise RuntimeError("Wrong social publishing policy; no posts sent.")
    if (policy.get("activePublisher") != "github-buffer-direct"
            or not policy.get("otherPublishers", {}).get("github_buffer_direct", {}).get("mayPublish", False)):
        print("SAFE HOLD: Food RSS publishing belongs to Zapier -> Buffer; GitHub direct queue is disabled.")
        return
    # Defense in depth: enable only after the Zapier RSS publisher is manually switched OFF.
    # Never backfill old public feed entries during cutover.
    cutover_raw = policy.get("githubBufferCutoverUtc")
    if not cutover_raw:
        print("SAFE HOLD: no verified Zapier-off cutover timestamp; no posting.")
        return
    cutover = dt.datetime.fromisoformat(cutover_raw.replace("Z", "+00:00"))
    if cutover.tzinfo is None:
        raise RuntimeError("Cutover timestamp must be UTC and timezone-aware")

    req = urllib.request.Request(FEED, headers={"User-Agent": "FoodBufferBridge/1.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        articles = read_feed(res.read(1600000))
    print("Public approved RSS articles:", len(articles))
    key = os.getenv("FOOD_BUFFER_API_KEY", "").strip()
    channel = (os.getenv("FOOD_BUFFER_CHANNEL_ID") or FOOD_CHANNEL_ID).strip()
    if channel != FOOD_CHANNEL_ID:
        raise RuntimeError("Food Buffer channel ID mismatch; no posts sent.")
    enabled = os.getenv("FOOD_BUFFER_AUTO_QUEUE", "").lower() == "true"
    if not (key and channel and enabled):
        print("SAFE MODE: missing credentials or enable flag; no Buffer posts created.")
        return
    ensure_channel(key, channel)
    scheduled = recent_posts(key, channel, "scheduled")
    if len(scheduled) >= 9:
        print("Buffer queue has at least 9 posts; skipping.")
        return
    sent = recent_posts(key, channel, "sent")
    buffer_text = "\n".join(str(p.get("text") or "") for p in scheduled + sent)
    history = json.loads(STATE.read_text("utf-8")) if STATE.exists() else {}
    seen = set(history.get("queued_urls", []))
    for article in articles:  # RSS feed is newest-first; post only AFTER verified Zapier-off cutoff
        if article["published"] <= cutover:
            continue
        url = article["url"]
        if url in seen:
            continue
        if url in buffer_text:
            seen.add(url)
            continue
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
        seen.add(url)
        break  # MAXIMUM ONE NEW POST PER RUN
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(
        json.dumps({"schema": 1, "site": SITE, "queued_urls": sorted(seen)},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved anti-duplicate state. No secrets stored.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Bridge safely stopped:", exc, file=sys.stderr)
        sys.exit(1)
