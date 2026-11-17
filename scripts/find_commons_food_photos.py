#!/usr/bin/env python3
"""ANW-09. Read-only discovery of Commons photos with machine-readable free licenses.
NEVER publishes, changes ready.json, claims photo matches a dish, or imports content.
"""
import hashlib
import html
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime,timezone
from pathlib import Path

SOURCE=Path("ready.json")
PUBLIC_MANIFEST=Path("out/manifest.json")
OUT=Path("reports/food-35-commons-photo-candidates.json")
API="https://commons.wikimedia.org/w/api.php"
USER_AGENT="Food35LicensedPhotoScout/1.0 (github.com/haidtbasaomh-blip/an-ngon-co-deal-content)"
# These are search aliases, not a claim that any returned file depicts the correct food.
ALIASES={
"xoi-xeo-buoi-sang":["xôi xéo","xoi xeo"],
"banh-gio-ha-noi":["bánh giò","banh gio"],
"bun-oc-ha-noi":["bún ốc","bun oc"],
"bun-moc-ha-noi":["bún mọc","bun moc"],
"chao-suon-buoi-chieu":["cháo sườn","chao suon"],
"nem-ran-bua-co":["nem rán","nem ran","spring rolls Vietnam"],
"banh-tom-ho-tay":["bánh tôm","banh tom"],
"o-mai-lam-qua":["ô mai","o mai vietnam"],
"banh-khuc-ha-noi":["bánh khúc","xôi khúc"],
"banh-ran-man":["bánh rán mặn","banh ran"],
"banh-troi-tau":["bánh trôi tàu","banh troi tau"],
"che-sen-ha-noi":["chè sen","che sen"],
"banh-com-lam-qua":["bánh cốm","banh com"],
"pho-cuon-ngu-xa":["phở cuốn","pho cuon"],
"pho-chien-phong":["phở chiên phồng","pho chien phong"],
"bun-bo-nam-bo-ha-noi":["bún bò nam bộ","bun bo nam bo"],
"nem-chua-ran":["nem chua rán","nem chua ran"],
"sua-chua-nep-cam":["sữa chua nếp cẩm","sua chua nep cam"],
"com-rang-dua-bo":["cơm rang dưa bò","com rang dua bo"],
"banh-mi-pate-ha-noi":["bánh mì","banh mi vietnam"],
"mien-luon":["miến lươn","mien luon"],
"bun-ngan":["bún ngan","bun ngan"],
"nuoc-sau-da":["nước sấu","nuoc sau"],
"tra-chanh-pho":["trà chanh","tra chanh"],
"banh-trang-tron-ha-noi":["bánh tráng trộn","banh trang tron"],
"che-khuc-bach":["chè khúc bạch","che khuc bach"],
"bo-bia-ngot":["bò bía ngọt","bo bia"],
"khoai-lang-nuong":["khoai lang nướng","grilled sweet potato"],
"dua-gop-an-kem":["dưa góp","dua gop"],
"sua-dau-nanh":["sữa đậu nành","soy milk vietnam"],
"bun-ca-cay-hai-phong":["bún cá cay","bun ca hai phong"],
"banh-da-cua":["bánh đa cua","banh da cua"],
"banh-xeo-mien-nam-ha-noi":["bánh xèo","banh xeo"],
"cha-muc-ha-long-lam-qua":["chả mực","cha muc"],
"banh-gai-lam-qua":["bánh gai","banh gai"]
}

def norm(s):
    t=unicodedata.normalize("NFKD",str(s).casefold())
    t="".join(c for c in t if not unicodedata.combining(c))
    t=t.replace("đ","d")
    return re.sub(r"[^a-z0-9]+"," ",t).strip()

def plaintext(s):
    return html.unescape(re.sub(r"<[^>]*>"," ",str(s or ""))).strip()[:300]

def val(d,key):
    return (d.get(key) or {}).get("value","") if isinstance(d,dict) else ""

def is_free_license(metadata):
    short=plaintext(val(metadata,"LicenseShortName"))
    low=norm(short)
    # No CC BY-NC, ND or unknown/no license; allow CC BY/SA/0 and PD only.
    if "nc" in low.split() or "nd" in low.split():return False,short
    allowed=("cc by ","cc by sa ","cc0","public domain","pd self","pd old","pd us")
    return any(low.startswith(s) for s in allowed),short

def get_results(search_term):
    query={
      "action":"query","format":"json","formatversion":"2",
      "generator":"search","gsrsearch":search_term,
      "gsrnamespace":"6","gsrlimit":"8",
      "prop":"imageinfo","iiprop":"url|size|mime|extmetadata",
      "iiurlwidth":"760"
    }
    url=API+"?"+urllib.parse.urlencode(query)
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=26) as r:
                if r.status!=200:raise RuntimeError("HTTP_NON_200")
                return json.load(r).get("query",{}).get("pages",[])
        except (urllib.error.URLError, TimeoutError, ValueError,RuntimeError):
            if attempt==2:raise
            time.sleep(2*(attempt+1))
    return []

def classify(page,aliases):
    info=(page.get("imageinfo") or [{}])[0]
    if not isinstance(info,dict):return None
    mime=str(info.get("mime") or "").lower()
    if mime not in ("image/jpeg","image/png","image/webp"):return None
    if int(info.get("width") or 0)<480 or int(info.get("height") or 0)<320:return None
    meta=info.get("extmetadata") or {}
    license_ok,license_name=is_free_license(meta)
    if not license_ok:return None
    attribution=plaintext(val(meta,"Attribution") or val(meta,"Artist"))
    if not attribution:return None
    pageurl=str(info.get("descriptionurl") or "")
    thumb=str(info.get("thumburl") or "")
    source=str(info.get("url") or "")
    if not pageurl.startswith("https://commons.wikimedia.org/wiki/File:"):return None
    if not source.startswith("https://upload.wikimedia.org/"):return None
    if thumb and not thumb.startswith("https://upload.wikimedia.org/"):return None
    fname=norm(page.get("title") or "")
    matched=[a for a in aliases if len(norm(a))>=5 and norm(a) in fname]
    if not matched:return None
    return {"commonsFile":page.get("title"),"filePage":pageurl,"imageUrl":thumb or source,
        "originalUrl":source,"license":license_name,
        "licenseUrl":plaintext(val(meta,"LicenseUrl")),
        "attribution":attribution,
        "width":info.get("width"),"height":info.get("height"),
        "matchBasis":"matching phrase in Commons filename, NOT visual validation",
        "visualDishIdentityVerified":False,
        "copyrightFieldsPresent":True}

def main():
    doc=json.loads(SOURCE.read_text(encoding="utf8"))
    ids=json.loads(PUBLIC_MANIFEST.read_text(encoding="utf8")).get("ids") or []
    if len(ids)!=35 or set(ids)!=set(ALIASES):
        raise RuntimeError("Expected exact 35 separate staging dishes, do not add other projects")
    byid={x.get("id"):x for x in doc["articles"]}
    if any(i not in byid for i in ids):raise RuntimeError("Missing staging dish")
    out={"asOf":datetime.now(timezone.utc).isoformat(),"target":"ANW-09",
      "scope":"35 unpublished Food staging articles only","automaticallyApproved":False,
      "productionChanged":False,"searchCount":0,"licensedCandidates":0,
      "dishImagesReadyToPublish":0,"items":[],"errors":[]}
    for dish_id in ids:
        article=byid[dish_id]
        aliases=ALIASES[dish_id]
        matches=[];failed=[]
        for term in aliases[:2]:
            try:
                pages=get_results(term)
                out["searchCount"]+=1
            except Exception as exc:
                failed.append(type(exc).__name__)
                continue
            for p in pages:
                c=classify(p,aliases)
                if c and not any(x["filePage"]==c["filePage"] for x in matches):
                    matches.append(c)
            if len(matches)>=3:break
            time.sleep(.14)
        out["items"].append({"id":dish_id,"title":article.get("title"),
            "previousImageType":article.get("imageType"),
            "reviewStatus":"NEEDS_MANUAL_VISUAL_DISH_MATCH",
            "licensingCandidates":matches[:4],
            "lookupErrors":failed})
    out["licensedCandidates"]=sum(len(x["licensingCandidates"]) for x in out["items"])
    out["dishesWithCandidate"]=sum(bool(x["licensingCandidates"]) for x in out["items"])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:v for k,v in out.items() if k not in ("items","errors")},ensure_ascii=False))
    print("No staging or live changes. File pages and rights require human dish-photo visual matching before applying.")
    if out["errors"]:print("Errors:",out["errors"][:3])

if __name__=="__main__":main()
