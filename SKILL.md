---
name: rednote-canvas
description: Turn articles, research, notes, data, or existing drafts into clear Xiaohongshu carousel storyboards and 1080×1350 image slides. Use when Codex needs to create, restructure, critique, or visually optimize 小红书图文、小红书轮播图、信息卡片、知识型笔记、研究型长图, including converting long-form content into 6–10 slides, improving an existing slide set, rendering local PNGs, or checking typography, density, hierarchy, overflow, and factual/source presentation.
---

# Rednote Canvas

Build a coherent carousel, not a collection of decorated paragraphs. Treat model interpretation, information architecture, visual hierarchy, deterministic rendering, and visual QA as one workflow. Constraints prevent accidents; a content-specific visual thesis creates meaning.

## Choose the task path

- For source material or a long article, extract the thesis and build a slide-by-slide narrative.
- For an existing outline or JSON spec, preserve the argument and improve page roles, density, and components.
- For existing images, inspect every image first. Diagnose hierarchy, spacing, contrast, consistency, clipping, and sequence before rebuilding.
- For a critique-only request, stop after the annotated diagnosis and prioritized fixes. Do not render unless requested.

Read [references/content-blueprints.md](references/content-blueprints.md) when deciding the story sequence. For reference-driven or visually ambitious work, read [references/model-interpretation.md](references/model-interpretation.md) and write the design manifest before styling. When photographs, illustrations, collage, expressive objects, or material texture could carry meaning, also read [references/image-led-design.md](references/image-led-design.md). Read [references/design-contract.md](references/design-contract.md), [references/layout-system.md](references/layout-system.md), and [references/visual-qa-rubric.md](references/visual-qa-rubric.md) before choosing styles or doing visual QA. Read [references/spec-format.md](references/spec-format.md) before writing a render spec.

## 1. Establish the content contract

Identify:

- audience and desired reader action;
- one-sentence thesis;
- facts, quotes, and sources that may be presented as verified;
- desired slide count, defaulting to 6–10 for a dense educational carousel;
- author/footer text and any provided brand constraints.

Infer these from supplied material when safe. Ask the human only when a missing choice would materially change the result. Never invent a statistic, quotation, source, credential, or platform rule to fill a layout.

## 2. Write the narrative before styling

Create a storyboard with exactly one sentence per slide describing that slide's job. Give each slide one dominant message and select only the components needed to prove it.

Prefer this rhythm for research-style content:

1. promise or tension;
2. evidence of relevance;
3. distinction or comparison;
4. mechanism or framework;
5. value, consequence, or case data;
6. disagreement or limitation;
7. the author's judgment and decision threshold;
8. deeper implication or local context;
9. conclusion and reader-specific action.

Shorten or merge roles when fewer pages are appropriate. Do not force nine pages when the material cannot support them.

## 3. Interpret the content visually

For reference-driven work, set `referenceDriven: true` and create a concise `designManifest`. The manifest records:

- one visual thesis and intended emotional progression;
- a semantic metaphor or a reason to use none;
- one or two meaningful motifs;
- deck rhythm, contrast plan, and type strategy;
- one composition intent per slide;
- recent habits and visual clichés to avoid;
- why this direction fits this specific content.

This is an inspectable design brief, not hidden reasoning. Use it to make decisions and later judge whether the render delivered the intended meaning.

Choose a `visualMode` before choosing blocks:

- `editorial` when language and evidence should remain primary;
- `mixed` when image and structure should alternate;
- `image-led`, `photo-diary`, `object-study`, or `poetic-poster` when a visual anchor should carry the page before explanatory text.

For any mode beyond `editorial`, add a short `materialSystem`, `imageCadence`, and per-slide `visualAnchor` plan to the manifest. Do not satisfy this step by placing generic AI decoration behind existing cards. Each image needs a semantic role: hero, evidence, atmosphere, texture, motif, or transition.

Before a full deck, create three two-page directions that differ in interpretation and composition—not merely colors. Prefer metaphor-led, typographic/editorial, and diagram/spatial directions when appropriate. Compare them with:

```bash
python3 <skill-dir>/scripts/compare_directions.py direction-a.json direction-b.json direction-c.json
```

If comparison reports `distinct: false`, revise the concepts or compositions before asking the human to choose a direction.

## 4. Apply a bounded visual system

Use a 1080×1350 canvas unless the user specifies another target. Default to the bundled editorial theme: warm paper background, near-black text, restrained brick-red accents, pale-yellow highlights, Chinese serif display type, and simple sans-serif labels.

Keep these constraints as guardrails, not a fixed template:

- one dominant headline per slide;
- two to four content modules per slide;
- no more than three highlight phrases per slide unless a table requires emphasis;
- source labels smaller than body copy but still legible;
- generous bottom clearance for platform overlays and pagination;
- alternating dense and light pages across the sequence.

For mixed or image-led decks:

- begin with the image-text relationship, not a component quota;
- avoid three consecutive pages that all require reading before seeing;
- include a low-text visual pause when the narrative can support one;
- limit the material vocabulary to two or three coherent treatments;
- preserve asymmetry, cropping, and negative space when they improve the idea;
- use original, user-provided, licensed, or public-domain assets only, and record provenance outside the slide when needed.

Choose composition primitives because they express a relationship. Available archetypes are starting points (`editorial`, `poster`, `split`, `diagram`, `timeline`, `custom`); primitives may be combined within safe bounds. A custom composition must explain why breaking the normal grid helps the content.

Abstract visual principles from references. Do not copy another creator's text, watermark, avatar, account name, signature, or distinctive identity treatment.

## 5. Create the render spec

Copy [assets/starter-carousel.json](assets/starter-carousel.json) into the working output directory and replace its original example content. Keep user material outside the Skill directory.

Use only the supported block types documented in [references/spec-format.md](references/spec-format.md), including the local-only `image` block. Treat all content as plain text; never insert user text into the HTML template as executable markup. Image sources must be local PNG, JPEG, WebP, or SVG paths relative to the spec or absolute local paths; remote URLs are rejected.

Run structural validation before rendering:

```bash
python3 <skill-dir>/scripts/render_carousel.py carousel.json --output-dir rendered --check-only
```

Fix every reported spec error before continuing.

## 6. Render deterministically

Render the deck with the bundled HTML/CSS template:

```bash
python3 <skill-dir>/scripts/render_carousel.py carousel.json --output-dir rendered
```

The renderer writes:

- `carousel.html`, the editable local preview;
- `slide-01.png`, `slide-02.png`, and so on;
- `qa.json`, including dimensions and overflow results.
- `design-manifest.json` for interpreted decks.

For interpreted decks, it also compares a non-sensitive visual fingerprint with the most recent five entries in `design-history.jsonl` beside the spec. This produces a review warning rather than prohibiting justified reuse. Pass `--no-history` only for fixtures or reproducible tests.

If Playwright or a Chromium browser is unavailable, report the exact missing prerequisite. Do not silently replace the renderer with AI-generated text images.

## 7. Perform visual QA

Read `qa.json`, then inspect the rendered PNGs visually. For a deck of ten pages or fewer, inspect every page. At minimum verify:

- title hierarchy and line breaks;
- no clipped or overlapping text;
- readable source labels and table cells;
- consistent margins, rules, card radii, and page numbers;
- restrained highlighting and accent usage;
- sequence-level density and rhythm;
- accurate author/footer text;
- absence of copied identity elements.
- semantic role, focal point, crop, and provenance of every image;
- whether the slide still carries mood or meaning when its explanatory copy is covered;
- absence of generic AI visual clichés used only as decoration;
- coherence of paper, ink, grain, tape, shadow, or other material treatments;
- sequence-level image cadence: no accidental return to a wall of text after an image-led opening.
- semantic fit between each page and its recorded composition intent;
- meaningful variation from recent decks without random novelty;
- at least one deliberate moment of contrast or surprise that serves the argument.

Read the three statuses separately: `structurally_valid` means the page did not break; `veg_review_required` remains true until review; `visually_approved` is never granted by the renderer. Do not accept a deck that merely passes overflow checks. Visual balance, awkward orphan lines, misleading emphasis, and a manifest that the render fails to express still require judgment. Revise the JSON and rerender until both automated and visual checks pass.

## 8. Deliver the working set

Return:

- the storyboard;
- the editable JSON spec;
- the rendered PNG directory;
- a concise QA summary;
- the design manifest and any recent-similarity warning;
- optional post caption and hashtags only when requested.

Keep publishing separate. Uploading or posting to Xiaohongshu is an external action and requires explicit authorization at action time.
