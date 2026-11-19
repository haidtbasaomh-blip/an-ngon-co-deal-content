#!/usr/bin/env python3
"""ANF-07: live Buffer Food queue/history deduplication audit, strictly READ ONLY.
Uses same verified Buffer channel and paginated reader as the production
approved-RSS publisher; does not call createPost or any write mutation.
"""
import hashlib,json,os,re,sys,urllib.request
from pathlib import Path
from food_buffer_rss import FOOD_CHANNEL_ID,SITE,FEED,ensure_channel,recent_posts,read_feed

def canonical_urls(text):
    urls=re.findall(r"https?://[^\s<>\")\]]+",str(text or ""),re.I)
    out=[]
    for url in urls:
        norm=url.rstrip(".,!;?").split("?",1)[0].split("#",1)[0]
        if norm.startswith(SITE+"/bai-viet/") and norm.endswith("/"):
            out.append(norm)
    return sorted(set(out))
def normhash(text):
    t=" ".join(str(text or "").split()).casefold()
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]

def main():
    key=os.getenv("FOOD_BUFFER_API_KEY","").strip()
    channel=(os.getenv("FOOD_BUFFER_CHANNEL_ID") or FOOD_CHANNEL_ID).strip()
    if not key:raise RuntimeError("FOOD_BUFFER_KEY_MISSING")
    if channel!=FOOD_CHANNEL_ID:raise RuntimeError("WRONG_FOOD_CHANNEL_ID")
    ensure_channel(key,channel)
    scheduled=recent_posts(key,channel,"scheduled")
    sent=recent_posts(key,channel,"sent")
    by_url={}
    by_hash={}
    for status,entries in [("scheduled",scheduled),("sent",sent)]:
        for item in entries:
            id=str(item.get("id") or "")
            content=str(item.get("text") or "")
            digest=normhash(content)
            by_hash.setdefault(digest,[]).append({"id":id,"status":status})
            for url in canonical_urls(content):
                by_url.setdefault(url,[]).append({"id":id,"status":status})
    duplicate_urls={u:v for u,v in by_url.items() if len(v)>1}
    duplicate_bodies={h:v for h,v in by_hash.items() if len(v)>1}
    req=urllib.request.Request(FEED,headers={"User-Agent":"Food-Buffer-ReadOnly-Dedupe-Audit/1"})
    with urllib.request.urlopen(req,timeout=20) as resp:
        articles=read_feed(resp.read(1600000))
    report={
        "mode":"read_only","channelVerified":"AN NGON CO DEAL Facebook via Buffer exact channel",
        "scheduledCount":len(scheduled),"sentCount":len(sent),
        "publicApprovedRssCount":len(articles),
        "distinctFoodCanonicalLinksInBuffer":len(by_url),
        "duplicateCanonicalCount":len(duplicate_urls),
        "duplicateContentHashCount":len(duplicate_bodies),
        "duplicateCanonicalPostRefs":{u:[v["status"] for v in posts] for u,posts in duplicate_urls.items()},
        "duplicateBodyHashes":{h:[v["status"] for v in posts] for h,posts in duplicate_bodies.items()},
        "autoPostingPaused":False,"writes":0,"secretsExposed":False,
        "note":"Live queue/history dedupe observation, not proof that a new approved article was replayed or posted. Do not count ANF-07 100% without an E2E replay."
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/food-anf07-buffer-live-dedupe-readonly.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ANF07_BUFFER_READONLY_AUDIT",json.dumps(report,ensure_ascii=False))
    if duplicate_urls or duplicate_bodies:
        raise RuntimeError("FOOD_BUFFER_DUPLICATE_QUEUED_OR_SENT")
if __name__=="__main__":
    main()
