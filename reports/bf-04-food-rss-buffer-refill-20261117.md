# BF-04 — Food RSS automatically refills Buffer queue without an open PC

Acceptance criterion from master 117: "Sau mỗi bài public, queue cập nhật không cần bật PC".
Evidence collected from connected app screenshots and live web/feed, Nov 15–17, 2026 (Asia/Bangkok).

**Source**: https://an-ngon-co-deal.bvthn-1903.chatgpt.site/rss.xml
**Zapier Cloud**: https://zapier.com/app/history — Zap named `Add new items in RSS feeds to Buffer as scheduled items`, trigger `RSS by Zapier / New Item in Feed` and action `Buffer / Add to Queue`.
- Successful history event 2026-11-15 at **10:15:09** (user-provided Zapier history screenshot 16/11).
- Successful history event 2026-11-15 at **14:26:54** (same screenshot).
- Zap editor's Buffer action `Channel` confirms exact target `Ăn Ngon Có Deal Facebook Page`; `Method = queue`, not PC GIÁ TỐT.
- Cloud-app steps execute independently of user's Windows PC/Chrome/ChatGPT Work.

**Destination**: https://publish.buffer.com/channels/6af914e962b70b94b0375e37/schedule?tab=sent
- User-provided Buffer screenshot 16/11: 4 Sent, 0 Queue, 0 Drafts. Sent includes Bún riêu Hà Nội and Bánh cuốn Thanh Trì sourced from food site's own posts.
- Facebook screenshot 16/11 shows both linked articles live on the exact official Food Page: https://www.facebook.com/profile.php?id=61596507422819
- At audit 17/11: /api/editorial = 53 public articles, all `approved=true` and `publicationStatus='published'`; RSS publicly accessible (HTTP 200).

**BF-04 verdict: PASS for observed cloud RSS-triggered-to-Buffer queue operation, two verified successful Zap runs and real Facebook delivery.**

Limitations not yet accepted:
- ANF-04 requires THREE successive new, distinct articles (2 observed Zap runs is not proof of 3).
- ZP-05 / BF-07 require deliberate duplicate/retry end-to-end trials; not proven.
- 100% Free longevity depends on Zapier post-trial plan; two-step RSS+Buffer is expected free, but account current trial still flagged on 16/11 and not yet verified after expiration.
- Reverse Facebook -> website webhook is premium and is a separate route, not covered by this BF-04 verdict.
