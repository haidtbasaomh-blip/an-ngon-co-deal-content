#!/usr/bin/env python3
"""Safe RSS -> Buffer queue for An Ngon Co Deal (never PC GIA TOT)."""
import html
import json
import os
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SITE = "https://an-ngon-co-deal.bvthn-1903.chatgpt.site"
FEED = SITE + "/rss.xml"
BUFFER = "https://api.buffer.com"
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
        articles.append({"url": url, "title": title, "summary": abstract[:330]})
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
    with urllib.request.urlopen(req, timeout=25) as res:
        output = json.load(res)
    if output.get("errors"):
        raise RuntimeError("Buffer GraphQL: " + str(output["errors"][0].get("message")))
    return output.get("data") or {}


def ensure_channel(key, channel_id):
    q = "query ($id: ChannelId!) { channel(input: {id: $id}) { id name displayName service } }"
    ch = graphql(key, q, {"id": channel_id}).get("channel") or {}
    label = str(ch.get("name") or "") + " " + str(ch.get("displayName") or "")
    if str(ch.get("id")) != channel_id:
        raise RuntimeError("Channel ID not confirmed. No posts sent.")
    if "facebook" not in str(ch.get("service") or "").lower():
        raise RuntimeError("Wrong channel type. No posts sent.")
    if "an ngon co deal" not in fold(label):
        raise RuntimeError("Wrong Fanpage! Must be An Ngon Co Deal. No posts sent.")


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
    req = urllib.request.Request(FEED, headers={"User-Agent": "FoodBufferBridge/1.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        articles = read_feed(res.read(1600000))
    print("Public food RSS articles:", len(articles))
    key = os.getenv("FOOD_BUFFER_API_KEY", "").strip()
    channel = os.getenv("FOOD_BUFFER_CHANNEL_ID", "").strip()
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
    for article in reversed(articles):
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
