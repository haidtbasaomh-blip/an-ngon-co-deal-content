#!/usr/bin/env python3
"""Read-only readiness check for moving Food RSS -> Buffer from Zapier to GitHub Free.

Never creates, schedules, edits, or deletes posts. No secrets or personal data
are logged; outputs only public feed counts and Boolean/channel status.
"""
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

SITE = "https://an-ngon-co-deal.bvthn-1903.chatgpt.site"
CHANNEL = "6af914e962b70b94b0375e37"
API = "https://api.buffer.com"


def gql(token, query):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query}).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            "User-Agent": "Food-GitHub-Free-ReadOnly/1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = json.load(r)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Buffer API HTTP {exc.code}") from None
    if body.get("errors"):
        raise RuntimeError("Buffer GraphQL schema/access rejected query")
    return body.get("data") or {}


def main():
    req = urllib.request.Request(
        SITE + "/rss.xml",
        headers={"User-Agent": "Food-GitHub-Free-ReadOnly/1"},
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read(1_500_000)
        if r.status != 200:
            raise RuntimeError("Food RSS not HTTP 200")
    root = ET.fromstring(raw)
    items = root.findall("./channel/item")
    good = [
        n for n in items
        if (n.findtext("link") or "").startswith(SITE + "/bai-viet/")
    ]
    print(f"PUBLIC_RSS: PASS ({len(good)} article references; no drafts inspected)")
    token = os.environ.get("FOOD_BUFFER_API_KEY", "").strip()
    if not token:
        print("BUFFER_API: MISSING GitHub Actions secret FOOD_BUFFER_API_KEY")
        return 2
    if token.lower().startswith("bearer "):
        print("BUFFER_API: INVALID format; GitHub secret must contain raw API key without Bearer prefix")
        return 3
    # Report only Boolean-quality categories; do not emit credential values.
    has_control = any(ord(ch) < 32 or ord(ch) == 127 for ch in token)
    looks_masked = any(marker in token for marker in ("••", "****", "...", "…", "<", ">"))
    if has_control or looks_masked or len(token) < 20:
        print("BUFFER_KEY_FORMAT: INVALID_OR_MASKED (no key disclosed)")
        return 8
    if token.lower().startswith("bearer ") or token.startswith(("'", '"')) or token.endswith(("'", '"')):
        print("BUFFER_KEY_FORMAT: WRAPPED_OR_PREFIXED (no key disclosed)")
        return 9
    print("BUFFER_KEY_FORMAT: plausible (no key disclosed)")
    try:
        result = gql(token, "query { account { organizations { id } } }")
        orgs = (result.get("account") or {}).get("organizations") or []
        if len(orgs) != 1:
            print("BUFFER_API: account has unexpected number of organizations")
            return 4
        oid = json.dumps(str(orgs[0]["id"]))
        query = "query { channels(input: {organizationId: " + oid + "}) { id name service } }"
        channels = gql(token, query).get("channels") or []
        channel = next((c for c in channels if str(c.get("id")) == CHANNEL), None)
        if not channel:
            print("BUFFER_CHANNEL: designated Food ID not found; no writes")
            return 5
        if str(channel.get("service", "")).lower() != "facebook":
            print("BUFFER_CHANNEL: expected Facebook service not found")
            return 6
        # Intentional: name is checked against expected exact page, not printed.
        import unicodedata
        def strip(s):
            return "".join(c for c in unicodedata.normalize("NFD", str(s).lower())
                           if not unicodedata.combining(c))
        if "an ngon co deal" not in strip(channel.get("name", "")):
            print("BUFFER_CHANNEL: Food Facebook channel display name mismatch")
            return 7
        print("BUFFER_API_AUTH: PASS")
        print("BUFFER_FOOD_CHANNEL: PASS (id + service + name)")
        # Limit to 2 statuses to minimize free-tier API usage.
        for st in ("sent", "scheduled"):
            post_query = ('query { posts(first: 20, input: {organizationId: ' + oid
                          + ', filter: {status: [' + st + '], channelIds: [' + json.dumps(CHANNEL)
                          + ']}}) { edges { node { id } } } }')
            posts = gql(token, post_query).get("posts") or {}
            print(f"BUFFER_{st.upper()}_READ: PASS (fetched {len(posts.get('edges', []))} records)")
        print("FREE_MIGRATION_READ_ONLY_READY: PASS; no Zapier or Buffer changes made")
        return 0
    except RuntimeError as err:
        print("BUFFER_API_READ_ONLY: FAIL - " + str(err))
        return 1


if __name__ == "__main__":
    sys.exit(main())
