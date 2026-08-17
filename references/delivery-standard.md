# Huatu delivery standard

The product is the rendered image set. HTML is the deterministic layout, preview, and reproduction layer; JSON is the editable source. Neither HTML nor JSON alone is a finished image delivery.

## Artifact states

- **concept** — thesis, storyboard, or direction exploration; no production claim.
- **draft** — editable spec or partial render; placeholders and known defects may remain.
- **candidate** — all pages render and structural QA passes, but visual review or final fixes remain.
- **release** — final PNGs are fresh, every page has been inspected, blocking findings are zero, and the delivery checker passes.
- **blocked** — a required render, dependency, permission, inspection, or verification step could not complete.

Unless the user explicitly asks for exploration, critique only, or a rough draft, creation and repair requests target **release**.

## Release definition of done

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

- Browser unavailable, Chromium crash, missing PNG, stale render, failed QA, or uninspected pages → **BLOCKED**, not release.
- Never substitute `--check-only`, an HTML file, a design manifest, or a verbal description for the requested images.
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

- editable `carousel.json`;
- local source assets used by the spec;
- `rendered/carousel.html` as editable preview;
- `rendered/slide-01.png` … final numbered PNG;
- `rendered/qa.json`;
- `rendered/design-manifest.json` for reference-driven work;
- `qa-summary.md` with the final visual verdict;
- optional storyboard and publishing copy when requested.

Publishing remains a separate human-authorized action.

## Delivery check

After the final visual review, run:

```bash
python3 <skill-dir>/scripts/check_delivery.py carousel.json \
  --output-dir rendered \
  --qa-summary qa-summary.md
```

Exit code `0` and `release_ready: true` mean the bundle satisfies the mechanical release gate. They do not authorize publication.
