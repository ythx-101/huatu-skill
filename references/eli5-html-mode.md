# ELI5 Visual Explainer HTML mode

Use this mode when the requested final product is a small, scrollable visual explanation rather than a Xiaohongshu image carousel. It adds a second product path; it does not replace or relax the carousel workflow.

## Choose the mode explicitly

- Choose **carousel** when the user needs numbered social images, a 1080×1350 deck, or an editable JSON render spec. The final product remains PNG.
- Choose **ELI5 HTML** when the user asks for an interactive-feeling (but no-JavaScript), responsive visual explanation that can be opened as one local file. The final product is the HTML itself; screenshots and `qa.json` are evidence.
- If the target medium is ambiguous and the choice materially changes delivery, ask before producing either.

## Narrative contract

Create 3–7 scene sections in reading order. Mark each scene with `class="scene"` or `data-scene`. Each scene must:

1. teach exactly one concept;
2. contain exactly one `h2` or `h3` scene heading;
3. lead with a large inline SVG or figure that makes a flow, comparison, layer, loop, timeline, or analogy visible;
4. use a short claim plus only the labels needed to read the visual;
5. hand one clear idea to the next scene.

A useful scene sentence is: “After this screen, the reader can explain ___.” If the blank needs “and,” split the scene. Prefer labels of 2–8 Chinese characters, one short paragraph, and generous negative space. Do not shrink copy to rescue a crowded scene.

## Visual grammars

Choose a grammar because it expresses the concept:

- **flow** — directional hand-off, with explicit start and destination;
- **compare** — two aligned conditions with one meaningful difference;
- **layers** — authority, responsibility, or abstraction stacked vertically;
- **loop** — a repeated cycle with a named return condition;
- **timeline** — ordered events where sequence matters;
- **analogy** — a familiar model paired with an explicit “where it stops matching” note.

Inline SVG should use `role="img"` and `aria-label` or `aria-labelledby`. Keep SVG text legible, preserve contrast, and never encode the only explanation through color. Decorative marks belong outside the teaching visual and must not masquerade as evidence.

## Facts, sources, and simplification boundary

- State only facts supported by the supplied material or a named source. Do not infer protocols, timing guarantees, encryption, delivery guarantees, or authority boundaries from a diagram.
- Include exactly one non-empty source region marked `id="sources"` or `data-sources`. Use visible bibliographic text. A remote hyperlink is unnecessary and is rejected by the checker; write the source title, owner, date/version, and URL as plain text only when useful.
- Include exactly one non-empty boundary region marked `id="simplification"` or `data-simplification`. Name what arrows, boxes, and omitted steps mean, and which implementation details the visual does **not** claim.
- Label conceptual diagrams as “概念图” when readers could mistake them for an implementation or protocol specification.

## Self-contained safety contract

The artifact is one UTF-8 HTML file with inline CSS and inline SVG. It must contain:

- `<!doctype html>`, a non-empty `html lang`, responsive viewport metadata, one `main`, and one `h1`;
- no JavaScript, event handlers, forms, frames, objects, embeds, meta refresh, remote fonts, stylesheets, media, imports, CSS `url()`, analytics, or network-loaded resources;
- no credentials, private keys, access tokens, host-local paths, private IDs, or QR codes;
- no remote navigation/resource attributes. Sources should remain visible text rather than active external links.

Use system font fallbacks. Make controls unnecessary: reading and scrolling must expose the whole explanation. The artifact must remain usable at 390×844 and 1365×768, with no horizontal overflow and no visible text below 12 CSS pixels.

## Build and validate

Start from `assets/eli5-explainer-starter.html`, replace its teaching content, and keep semantic markers intact.

Static preflight only:

```bash
python3 <skill-dir>/scripts/check_explainer.py explainer.html --check-only
```

Real browser validation:

```bash
python3 <skill-dir>/scripts/check_explainer.py explainer.html \
  --output-dir explainer-qa
```

The second command must launch Chromium at 390×844 and 1365×768 and write:

- `qa.json` with static facts, per-viewport overflow/text checks, browser errors, external request attempts, screenshot hashes and dimensions;
- `preview-mobile.png`;
- `preview-desktop.png`.

The check fails closed on static policy errors, browser launch/render failure, any unsafe request attempt, horizontal overflow, browser errors, text below 12px, or missing/empty screenshots. `--check-only` is preflight, never final evidence. `valid: true` proves mechanical integrity, not visual quality.

## Review and delivery

Open the final HTML in a real browser and inspect both screenshots, mobile first. Verify first-screen comprehension, scene order, visual dominance, source and boundary legibility, obvious clipping, and whether each picture teaches rather than decorates. After the last HTML change, rerun browser validation and repeat inspection.

Deliver the HTML as the explainer product and the QA directory as evidence. Never substitute screenshots for the HTML or claim that screenshots are the product.

## Moshi Browser Preview (human-gated)

The parent/release owner may preview the reviewed artifact on iPhone through the existing Moshi SSH-forwarded preview path:

1. From the artifact root, start a temporary server bound only to loopback, for example `python3 -m http.server 5173 --bind 127.0.0.1`.
2. Open `http://127.0.0.1:5173/<path-to-explainer.html>` through Moshi Browser Preview.
3. Check portrait reading order, text size, clipping, scroll rhythm, and safe-area comfort.
4. Stop the server immediately after review.

Do not bind to `0.0.0.0`, create a public tunnel, use Tailscale Funnel, or treat desktop screenshots as iPhone acceptance. Starting the preview and approving the phone result remain human-owned actions.
