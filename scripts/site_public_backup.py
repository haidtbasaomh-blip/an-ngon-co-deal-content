#!/usr/bin/env python3
"""Read-only public website snapshot; never copies secrets, private drafts or database credentials."""
from __future__ import annotations
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

BASE = os.environ["SITE_BASE"].rstrip("/")
PROJECT = os.environ["BACKUP_PROJECT"]
OUT = Path("backups/public-site")
OUT.mkdir(parents=True, exist_ok=True)
REQUIRED = ("/", "/rss.xml", "/sitemap.xml")
EXTRAS = ("/robots.txt",)
metadata = {"project": PROJECT, "source": BASE, "capturedAt": datetime.now(timezone.utc).isoformat(),
            "scope": "PUBLIC ONLY - no D1, R2 drafts, private media, secrets, Buffer or Facebook",
            "files": {}, "counts": {}, "warnings": []}

def grab(path: str, target: str, required: bool = True):
    url = BASE + path
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "OwnerRecoveryPublicBackup/1.0", "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=25) as res:
                data = res.read(8_000_000)
                if res.status != 200 or not data:
                    raise RuntimeError("HTTP "+str(res.status)+" or empty response")
                fp = OUT / target
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_bytes(data)
                metadata["files"][target] = {"url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                return data
        except Exception as exc:
            last = type(exc).__name__ + ": " + str(exc)
            if attempt < 2:
                time.sleep(attempt + 1)
    if required:
        raise RuntimeError("Required public page failed: "+path+" "+str(last))
    metadata["warnings"].append(path+": "+str(last))
    return None

for route, name in (("/", "homepage.html"), ("/rss.xml", "rss.xml"), ("/sitemap.xml", "sitemap.xml")):
    body = grab(route, name)
    if route == "/rss.xml":
        root = ET.fromstring(body)
        count = len(root.findall("./channel/item"))
        if count == 0:
            raise RuntimeError("Public RSS unexpectedly empty")
        metadata["counts"]["rssArticles"] = count
    elif route == "/sitemap.xml":
        root = ET.fromstring(body)
        count = len(root.findall(".//{*}loc"))
        if count == 0:
            raise RuntimeError("Public sitemap unexpectedly empty")
        metadata["counts"]["sitemapUrls"] = count
for route in EXTRAS:
    grab(route, route.lstrip("/"), required=False)

if PROJECT == "pc-gia-tot":
    for path, filename in (("/api/public/build","build.json"), ("/api/public/lazada-status","lazada-status.json")):
        raw=grab(path,filename)
        json.loads(raw)
    public=[]
    seen=set()
    for page in range(1,51):
        path="/api/public/products?limit=15&page="+str(page)
        raw=grab(path, "product-pages/page-"+str(page).zfill(2)+".json")
        doc=json.loads(raw)
        batch=doc.get("items") or []
        for item in batch:
            slug=str(item.get("slug") or "")
            if not slug or slug in seen:
                raise RuntimeError("Missing/duplicate public product slug in backup: "+slug)
            seen.add(slug)
            public.append(item)
        if not doc.get("has_more") or not batch:
            break
    if not public:
        raise RuntimeError("No public products backed up")
    (OUT/"products-merged.json").write_text(json.dumps({"items": public, "count":len(public)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    metadata["counts"]["publicProducts"]=len(public)
    grab("/api/public/posts?limit=24&page=1", "public-posts-page-1.json", required=False)
else:
    raw=grab("/api/editorial", "published-editorial.json")
    parsed=json.loads(raw)
    if not isinstance(parsed.get("articles"),list):
        raise RuntimeError("Published editorial API missing articles array")
    metadata["counts"]["publicEditorial"]=len(parsed["articles"])
    if not parsed["articles"]:
        raise RuntimeError("Published articles unexpectedly empty")

(OUT/"BACKUP_SCOPE.txt").write_text(
    "PUBLIC-ONLY EMERGENCY SNAPSHOT. Does NOT include Cloudflare D1 database, private R2 food drafts/assets, private Cloudflare environment, Meta/Buffer/Metricool credentials or scheduled post state. Do not delete production databases or restore solely from this snapshot.\n",
    encoding="utf-8")
(OUT/"manifest.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"project":PROJECT,"status":"PASS","counts":metadata["counts"],"files":len(metadata["files"]),"warnings":metadata["warnings"]},ensure_ascii=False))
