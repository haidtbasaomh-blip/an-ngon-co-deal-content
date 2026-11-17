# ANW-18 — WCAG fix validated in disposable browser; NOT YET DEPLOYED

## Source production issues (17/11/2026)
- https://github.com/haidtbasaomh-blip/an-ngon-co-deal-content/actions/runs/43991691727
- axe-core finds two serious categories in Food homepage: low text color contrast in section/feature descriptions and card badges, and accessible name of home logo link does not contain its visible brand text.
- Other serious/critical WCAG categories: none in the tested sample.

## Tested exact patch (no changes to production)
Add CSS to the existing Food Site global stylesheet:

```css
.wrap > .section-head > div > p { color: #445144; }
.feature-content > p { color: #445144; }
.card-bottom > .badge { color: #65410d; }
```

Remove `aria-label="Trang chủ"` from the logo's home `<a>` when the anchor contains the visible brand name, so its natural accessible name matches the visible text. Do not remove useful aria labels from icon-only buttons.

## Evidence
- https://github.com/haidtbasaomh-blip/an-ngon-co-deal-content/actions/runs/43994375980
- Live HTML was loaded into an isolated Playwright context, patch was injected only in browser memory, and re-tested with `@axe-core/playwright`.
- Before: 5 color-contrast nodes + 1 label-name mismatch node.
- After: **zero serious/critical axe findings**, no production mutation.

## Remaining steps for 100% ANW-18
1. Use native ChatGPT Sites project `Ăn Ngon Có Deal`, edit **existing** site, not a new site.
2. Apply the CSS and anchor fix to the live source; keep all 53 public articles and 2,000 drafts untouched.
3. Re-run `.github/workflows/food-browser-a11y.yml` against real production on 375/390/mobile and 1440/desktop, check admin 403, broken images, keyboard focus, page-level JS errors, contrast, and report PASS.
4. The page-speed condition also requires a separate live mobile performance measurement, not just this a11y check.

**CURRENT STATUS:** NOT DONE. This is an exact tested patch ready for deployment, not acceptance evidence for live production.
