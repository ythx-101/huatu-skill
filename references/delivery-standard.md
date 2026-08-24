# Huatu delivery standard

Huatu has two explicit products:

- **Carousel:** the rendered PNG set is the product. HTML is the deterministic layout/preview layer and JSON is the editable source. Neither HTML nor JSON alone is a finished carousel delivery.
- **ELI5 Visual Explainer:** one self-contained responsive HTML file is the product. `qa.json` and mobile/desktop screenshots are verification evidence, not substitutes for the HTML.

Select the product mode before building; do not silently convert one into the other.

## Artifact states

- **concept** — thesis, storyboard, or direction exploration; no production claim.
- **draft** — editable spec or partial render; placeholders and known defects may remain.
- **candidate** — all pages render and structural QA passes, but visual review or final fixes remain.
- **release** — final PNGs are fresh, every page has been inspected, blocking findings are zero, and the delivery checker passes.
- **blocked** — a required render, dependency, permission, inspection, or verification step could not complete.

Unless the user explicitly asks for exploration, critique only, or a rough draft, creation and repair requests target **release**.

## ELI5 explainer definition of done

An explainer is mechanically release-ready only when all of the following are true:

1. The final UTF-8 HTML contains 3–7 semantic scenes, one concept and visual teaching element per scene, explicit sources, and an explicit simplification boundary.
2. It contains inline CSS/SVG only, with no JavaScript, remote/request-capable dependency, analytics, credential, token, host secret, private ID, or QR code.
3. `check_explainer.py --check-only` passes as preflight.
4. Real Chromium validation passes at 390×844 and 1365×768 and writes fresh `qa.json`, `preview-mobile.png`, and `preview-desktop.png`.
5. QA reports `valid: true`, `browser_valid: true`, no unsafe request attempts, browser errors, horizontal overflow, or visible text below 12px; both screenshots are non-empty.
6. A reviewer opens the HTML and inspects both screenshots after the last change for comprehension, reading order, clipping, density, source legibility, and visual teaching value.
7. Any required Moshi/iPhone check is completed by the parent/release owner. Desktop Chromium evidence does not impersonate phone acceptance.

Browser/dependency failure means **blocked**. `--check-only` is never final evidence. For the full content and preview procedure, read [eli5-html-mode.md](eli5-html-mode.md).

## Carousel release definition of done

A carousel is release-ready only when all of the following are true:

1. The editable JSON spec contains the final copy and local assets—no placeholders, stale environment snapshots, or knowingly temporary claims.
2. `render_carousel.py --check-only` passes. This is a preflight, not approval.
3. A real browser render produces `carousel.html`, `qa.json`, and every numbered PNG.
4. `qa.json` reports `valid: true`, `structurally_valid: true`, and no errors.
5. A reviewer visually inspects every PNG after the last render at 1× phone size and records `VERDICT: PASS` with `BLOCKING: none` in `qa-summary.md`.
6. The rendered outputs are newer than the spec and all local image/SVG sources.
7. `scripts/check_delivery.py` returns `release_ready: true`.

A warning may remain only when it is visually reviewed, explained in `qa-summary.md`, and does not contradict the comprehension gates.

## Fail-closed rules

- Browser unavailable, Chromium crash, missing target artifact/evidence, stale render, failed QA, or uninspected output → **BLOCKED**, not release.
- Never substitute `--check-only`, a design manifest, screenshots, or a verbal description for the requested product. Carousel HTML is not final PNG; explainer screenshots are not final HTML.
- Never say “done” and then list rendering or inspection as future work.
- Do not lower font size, hide overflow, or remove evidence merely to make automated QA green.
- Do not grant yourself visual approval by editing renderer-owned `qa.json`; visual approval lives in the human-readable QA summary and delivery evidence.

## Product-first review order

Review in this order to avoid rationale bias:

1. final PNGs or the target artifact;
2. phone-size scan and reading order;
3. sequence rhythm and cross-page coherence;
4. `qa.json` and source claims;
5. design manifest and author rationale.

If the visible product conflicts with the rationale, the product wins and must be revised.

## Required release bundle

Carousel:

- editable `carousel.json` and local source assets;
- `rendered/carousel.html` as editable preview;
- `rendered/slide-01.png` … final numbered PNG;
- `rendered/qa.json`, reference-driven `design-manifest.json`, and `qa-summary.md`.

ELI5 explainer:

- final self-contained `explainer.html`;
- `qa.json`, `preview-mobile.png`, and `preview-desktop.png` from the final browser run;
- human visual review evidence and optional parent-owned phone acceptance evidence.

Publishing and public serving remain separate human-authorized actions.

## Delivery check

After the final visual review, run:

```bash
python3 <skill-dir>/scripts/check_delivery.py carousel.json \
  --output-dir rendered \
  --qa-summary qa-summary.md
```

Exit code `0` and `release_ready: true` mean the bundle satisfies the mechanical release gate. They do not authorize publication.
