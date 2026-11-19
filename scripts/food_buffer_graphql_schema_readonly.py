#!/usr/bin/env python3
"""Read-only Buffer GraphQL schema field discovery for Food dedupe, no mutations."""
import json,os
from pathlib import Path
from food_buffer_rss import graphql
key=os.getenv("FOOD_BUFFER_API_KEY","").strip()
if not key:raise RuntimeError("BUFFER_KEY_UNAVAILABLE")
q="""query {
  postType: __type(name:"Post") {name fields {name type {kind name ofType {name kind}}}}
  createType: __type(name:"CreatePostInput") {name inputFields {name type {kind name ofType {name kind}}}}
}"""
try:
    d=graphql(key,q)
    fields=sorted((a.get("name") or "") for a in ((d.get("postType") or {}).get("fields") or []))
    create=sorted((a.get("name") or "") for a in ((d.get("createType") or {}).get("inputFields") or []))
    report={"mode":"READ_ONLY","postFields":fields,"createPostInputFields":create,
      "textAvailabilityAlternatives":[x for x in fields if any(y in x.lower() for y in ("text","media","content","asset","link","url","metadata","source"))],
      "serverIdempotencyInputCandidates":[x for x in create if any(y in x.lower() for y in ("key","external","idempot","dedup","source"))],
      "writes":0,"credentialsLogged":False}
except RuntimeError:
    report={"mode":"READ_ONLY","schemaAvailable":False,"reason":"Buffer GraphQL introspection unavailable","writes":0}
Path("reports").mkdir(exist_ok=True)
Path("reports/food-buffer-graphql-schema-readonly.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("BUFFER_SCHEMA_SAFE_SUMMARY",json.dumps(report,ensure_ascii=False))
