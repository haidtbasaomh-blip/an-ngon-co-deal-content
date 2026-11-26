#!/usr/bin/env python3
"""Prepare a read-only, idempotent staging feed for the existing ĂN NGON CÓ DEAL Site.

This script deliberately DOES NOT publish to ChatGPT Sites. It creates the
data that the existing Site can import after its owner enables an authorized
integration. Zero third-party Python dependencies.
"""
import argparse
import hashlib
import json
import re
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

SITE = "https://an-ngon-co-deal.bvthn-1903.chatgpt.site/"
SOURCE = Path("ready.json")
OUT = Path("out")


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != data:
        path.write_text(data, encoding="utf-8")


def clean_title(title):
    text = unicodedata.normalize("NFKD", title.lower().strip())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def check_article(article):
    slug = article.get("id", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError(f"Invalid slug {slug!r}")
    for field in ("title", "intro", "body", "category"):
        if not isinstance(article.get(field), str) or not article[field].strip():
            raise ValueError(f"Missing {field} for {slug}")
    if len(article["title"].strip()) < 10 or len(article["body"].strip()) < 700:
        raise ValueError(f"Incomplete editorial content for {slug}")
    if article.get("approved") is not True or article.get("editorialStatus") != "approved":
        raise ValueError(f"Not editorially approved: {slug}")
    if article.get("publicationStatus") != "ready_for_site":
        raise ValueError(f"Not staging-only: {slug}")
    if article.get("affiliateLinks"):
        raise ValueError(f"Unverified affiliate URL in {slug}")
    if re.search(r"(?i)(api[_-]?key|secret|token)\s*[:=]", article["body"]):
        raise ValueError(f"Potential secret in {slug}")
    return slug


def read_live():
    url = SITE + "api/editorial"
    req = urllib.request.Request(url, headers={
        "User-Agent": "AnNgonCoDealEditorialAudit/1.0",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            body = response.read(2_000_000)
        d = json.loads(body)
        if d.get("ok") is not True or not isinstance(d.get("articles"), list):
            return None, "Site editorial response malformed; no publish attempted"
        return d["articles"], None
    except Exception as exc:
        return None, f"Live site audit unavailable ({type(exc).__name__}); no publish attempted"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(SOURCE))
    parser.add_argument("--output", default=str(OUT))
    parser.add_argument("--offline", action="store_true",
                        help="Run without live Site comparison")
    args = parser.parse_args()
    source = Path(args.input)
    out = Path(args.output)
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or data.get("site") != SITE:
        raise ValueError("Wrong Site / schema. Do not mix with PC GIÁ TỐT.")
    if data.get("status") != "ready_for_site":
        raise ValueError("Expected ready_for_site, never assume public")
    articles = data.get("articles")
    if not isinstance(articles, list) or not (1 <= len(articles) <= 10_000):
        raise ValueError("Bad article count")
    if len(articles) != data.get("articleCount"):
        raise ValueError("articleCount mismatch")

    ids = []
    titles = []
    for a in articles:
        ids.append(check_article(a))
        titles.append(clean_title(a["title"]))
    if len(ids) != len(set(ids)) or len(titles) != len(set(titles)):
        raise ValueError("Duplicate IDs or normalized titles in staging")

    live_articles, live_error = (None, "offline audit") if args.offline else read_live()
    live_by_id = {a.get("id"): a for a in live_articles} if live_articles is not None else {}
    already_published = []
    for article in articles:
        live_item = live_by_id.get(article["id"])
        if live_item is None:
            continue
        # Exclude only a verified publication of the SAME titled, approved article.
        # Any ambiguous ID collision must fail safely rather than overwrite a Site page.
        if (live_item.get("approved") is not True
                or live_item.get("publicationStatus") != "published"
                or clean_title(live_item.get("title", "")) != clean_title(article["title"])):
            raise ValueError("LIVE Site ID collision/approval mismatch: " + article["id"])
        already_published.append(article["id"])
    if already_published:
        print("Already published on Site, excluded from staging:", already_published)
        articles = [a for a in articles if a["id"] not in set(already_published)]

    counts = dict(sorted(Counter(a["category"] for a in articles).items()))
    no_source = [a["id"] for a in articles if not a.get("source") or a.get("sourceStatus") != "topic_matched"]
    no_image = [a["id"] for a in articles if not a.get("image") and not a.get("imageUrl")]
    no_dish_photos = [a["id"] for a in articles if a.get("imageType") != "licensed_dish_photo"]
    warnings = []
    if no_source:
        warnings.append(f"{len(no_source)} stories have no cited source; recheck factual statements")
    if no_image:
        warnings.append(f"{len(no_image)} stories have no cover illustration")
    if no_dish_photos:
        warnings.append(f"{len(no_dish_photos)} stories still have no licensed dish photo; editorial SVGs are not photos")
    if live_error:
        warnings.append(live_error)

    staging = {
        "schema": 1,
        "site": SITE,
        "status": "ready_for_site",
        "articleCount": len(articles),
        "articles": articles,
    }
    save_json(out / "ready.json", staging)
    batches = []
    for index, begin in enumerate(range(0, len(articles), 100), 1):
        batch = articles[begin:begin + 100]
        path = f"batches/batch-{index:03d}.json"
        save_json(out / path, {
            "schema": 1,
            "site": SITE,
            "status": "ready_for_site",
            "articleCount": len(batch),
            "articles": batch,
        })
        batches.append({"path": path, "articleCount": len(batch)})
    # Explicit one-at-a-time handoff for the existing Sites editor. The
    # original staging queue and owner approvals are never modified here.
    # Do not equate a decorative cover with a verified dish photograph.
    eligible = []
    for item in articles:
        evidence = item.get("imageReview") or {}
        if (item.get("sourceStatus") == "topic_matched"
                and (item.get("sourceReview") or {}).get("verified") is True
                and item.get("imageType") == "licensed_dish_photo"
                and evidence.get("visualDishIdentityVerified") is True
                and evidence.get("commercialReuseLicenseVerified") is True
                and evidence.get("originalImageUnmodified") is True
                and evidence.get("requiresVisibleAttribution") is True
                and all(isinstance(item.get(k), str) and item[k].strip()
                        for k in ("imageUrl","imageAlt","imageCredit","imageSourcePage","imageLicenseUrl"))
                and all(item[k].startswith("https://") for k in
                        ("imageUrl","imageSourcePage","imageLicenseUrl"))):
            eligible.append(item)
    # Live comparison is mandatory; an unavailable inventory must not
    # release an article into the site editor queue.
    chosen = eligible[:1] if live_articles is not None else []
    save_json(out / "site_import_candidate.json", {
        "schema": 1,
        "site": SITE,
        "status": "ready_for_site",
        "mode": "one_owner_approved_article_editor_handoff",
        "articleCount": len(chosen),
        "articles": chosen,
        "eligibleStagingCount": len(eligible),
        "heldForPhotoOrSourceReview": len(articles) - len(eligible),
        "liveInventoryVerified": live_articles is not None,
        "sitePublicationConfirmed": False,
        "mustRenderVisibleAttribution": True,
        "mustRecheckLiveBeforeImport": True,
        "autoPublish": False,
    })
    print("SITE_EDITOR_CANDIDATE", json.dumps({"eligible":len(eligible),
          "selected":len(chosen),"held":len(articles)-len(eligible),
          "ids":[x["id"] for x in chosen],"liveInventoryVerified":live_articles is not None,
          "published":0},ensure_ascii=False))
    payload = json.dumps(staging, sort_keys=True, ensure_ascii=False).encode("utf-8")
    save_json(out / "manifest.json", {
        "schema": 1,
        "site": SITE,
        "stage": "ready_for_site",
        "sitePublicationConfirmed": False,
        "countReady": len(articles),
        "liveArticleCountAtLastAudit": len(live_articles) if live_articles is not None else None,
        "categories": counts,
        "batches": batches,
        "ids": [a["id"] for a in articles],
        "alreadyPublishedIds": already_published,
        "alreadyPublishedCount": len(already_published),
        "sourceSha256": hashlib.sha256(payload).hexdigest(),
        "missingSources": len(no_source),
        "missingImages": len(no_image),
        "missingSpecificDishPhotos": len(no_dish_photos),
        "warnings": warnings,
    })
    print(f"PASS: {len(articles)} validated staging articles in {len(batches)} batch(es)")
    print(f"LIVE SITE: {len(live_articles) if live_articles is not None else 'not checked'}")
    print(f"SOURCE/IMAGES FLAGGED: {len(no_source)}/{len(no_image)}")
    print("NOT PUBLISHED: ChatGPT Sites requires its own authorized integration.")


if __name__ == "__main__":
    main()
