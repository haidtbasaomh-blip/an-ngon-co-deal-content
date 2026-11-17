#!/usr/bin/env python3
"""Verify candidate pre-existing GitHub secret aliases against Buffer read-only API.
Does not reveal any secret bytes, lengths, prefixes or hashes. No mutations.
"""
import json
import os
import urllib.error
import urllib.request

NAMES = ("FOOD_BUFFER_API_KEY", "BUFFER_API_KEY", "BUFFER_ACCESS_TOKEN", "PCGT_BUFFER_API_KEY", "PC_BUFFER_API_KEY")
API = "https://api.buffer.com"
QUERY = {"query": "query { account { organizations { id } } }"}

results = {}
for name in NAMES:
    token = os.environ.get(name, "").strip()
    if not token:
        results[name] = "ABSENT"
        continue
    if token.lower().startswith("bearer "):
        results[name] = "INVALID_PREFIX"
        continue
    req = urllib.request.Request(
        API, data=json.dumps(QUERY).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer "+token,"User-Agent":"FoodBufferExistingSecretAliasCheck/1"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        if data.get("errors") or not (data.get("data",{}).get("account") or {}).get("organizations"):
            results[name] = "NO_ACCOUNT"
        else:
            results[name] = "AUTH_OK"
    except urllib.error.HTTPError as e:
        results[name] = "HTTP_"+str(e.code)
    except Exception as e:
        results[name] = "NETWORK_OR_PARSE_ERROR_"+type(e).__name__

print(json.dumps(results, sort_keys=True))
print("READ_ONLY: Buffer account/organization only; did not enqueue any posts; no secret values printed.")
if "AUTH_OK" not in results.values():
    raise SystemExit("No authorized existing GitHub Actions Buffer API secret; keep Zapier live.")
