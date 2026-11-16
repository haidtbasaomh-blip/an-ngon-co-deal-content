#!/usr/bin/env python3
"""Simulate restoring the public-site backup in an isolated temporary directory."""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

src=Path("backups/public-site")
manifest=json.loads((src/"manifest.json").read_text(encoding="utf-8"))
files=manifest.get("files",{})
if not all(k in files for k in ("homepage.html","rss.xml","sitemap.xml")):
    raise SystemExit("Missing minimum backup files")
for name,meta in files.items():
    p=src/name
    if not p.is_file():
        raise SystemExit("Missing backup: "+name)
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=meta["sha256"] or len(data)!=meta["bytes"]:
        raise SystemExit("Backup file hash/size mismatch: "+name)
with tempfile.TemporaryDirectory(prefix="restore-drill-") as td:
    root=Path(td)/"site"
    shutil.copytree(src,root)
    html=(root/"homepage.html").read_text(encoding="utf-8",errors="replace").lower()
    if "<html" not in html:
        raise SystemExit("Restored homepage invalid")
    rss=ET.fromstring((root/"rss.xml").read_bytes())
    if rss.tag!="rss":
        raise SystemExit("Restored RSS invalid")
    count=len(rss.findall("./channel/item"))
    if count!=manifest["counts"]["rssArticles"]:
        raise SystemExit("Restored RSS count mismatch")
    site=ET.fromstring((root/"sitemap.xml").read_bytes())
    sitemap_count=len(site.findall(".//{*}loc"))
    if sitemap_count!=manifest["counts"]["sitemapUrls"]:
        raise SystemExit("Restored sitemap count mismatch")
    if manifest["project"]=="pc-gia-tot":
        p=json.loads((root/"products-merged.json").read_text(encoding="utf-8"))
        if len(p.get("items") or [])!=manifest["counts"]["publicProducts"]:
            raise SystemExit("Restored product list incomplete")
    else:
        p=json.loads((root/"published-editorial.json").read_text(encoding="utf-8"))
        if len(p.get("articles") or [])!=manifest["counts"]["publicEditorial"]:
            raise SystemExit("Restored public editorial incomplete")
print(json.dumps({"status":"PASS","project":manifest["project"],"filesVerified":len(files),
 "restoredArticles":count,"restoredSitemapUrls":sitemap_count,
 "warning":"Public-only restore drill. D1, R2, secrets and actual Cloudflare deployment require separate backups."}))
