---
name: huatu-skill
description: Turn articles, research, notes, data, or existing drafts into clear Xiaohongshu carousel storyboards and 1080×1350 image slides. Use when Codex needs to create, restructure, critique, or visually optimize 小红书图文、小红书轮播图、信息卡片、知识型笔记、研究型长图, including converting long-form content into 6–10 slides, improving an existing slide set, rendering local PNGs, or checking typography, density, hierarchy, overflow, and factual/source presentation.
---

# 画图 Skill

Build a carousel that helps the reader understand the meaning — before it looks coherent, before it passes the rules. A deck succeeds when the layout itself makes a relationship, mechanism, or judgment easier to see than the text alone would. Treat model interpretation, information architecture, visual hierarchy, deterministic rendering, and visual QA as one workflow. Constraints are guardrails, not goals: they prevent accidents, but a content-specific visual thesis creates meaning. When a rule and the reader's comprehension conflict, the rule yields.

## Choose the task path

- For 知识型、机制型或研究型内容，默认选择 `mixed`（图文交替），并同时阅读 [references/image-led-design.md](references/image-led-design.md) 与 [references/diagram-system.md](references/diagram-system.md)；只有用户显式要求全文字时才选择 `editorial`。
- For source material or a long article, extract the thesis and build a slide-by-slide narrative.
- For an existing outline or JSON spec, preserve the argument and improve page roles, density, and components.
- For existing images, inspect every image first. Diagnose hierarchy, spacing, contrast, consistency, clipping, and sequence before rebuilding.
- For a critique-only request, stop after the annotated diagnosis and prioritized fixes. Do not render unless requested.

Read [references/content-blueprints.md](references/content-blueprints.md) when deciding the story sequence. For reference-driven or visually ambitious work, read [references/model-interpretation.md](references/model-interpretation.md) and write the design manifest before styling. When photographs, illustrations, collage, expressive objects, or material texture could carry meaning, also read [references/image-led-design.md](references/image-led-design.md). Read [references/kami-design.md](references/kami-design.md) (默认主题 v2.0 法则与 tokens), [references/design-contract.md](references/design-contract.md), [references/layout-system.md](references/layout-system.md), and [references/visual-qa-rubric.md](references/visual-qa-rubric.md) before choosing styles or doing visual QA. Read [references/spec-format.md](references/spec-format.md) before writing a render spec.

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

知识型、机制型和研究型内容默认使用 `mixed`；只有用户显式选择 `editorial` 时才改为全文字路径。任何非 `editorial` 模式的 manifest **必须**包含简短的 `materialSystem`、`imageCadence` 与逐页 `visualAnchor` 计划，不能只写一个模式名称。Do not satisfy this step by placing generic AI decoration behind existing cards. Each image needs a semantic role: hero, evidence, atmosphere, texture, motif, or transition.

Before a full deck, create three two-page directions that differ in interpretation and composition—not merely colors. Prefer metaphor-led, typographic/editorial, and diagram/spatial directions when appropriate. Compare them with:

```bash
python3 <skill-dir>/scripts/compare_directions.py direction-a.json direction-b.json direction-c.json
```

If comparison reports `distinct: false`, revise the concepts or compositions before asking the human to choose a direction.

## 4. Apply a bounded visual system

Use a 1080×1350 canvas unless the user specifies another target. For a single 3:4 cover (e.g. Xiaohongshu 封面), set the top-level `canvas` field to `{"width": 1080, "height": 1440}` and render a one-slide poster spec. **Default theme is Kami (v2.0)**: warm parchment canvas, ink-blue accent, warm-gray text scale, serif-led hierarchy (weight 500, no pseudo-bold), hairline borders, whisper-only shadows, no default italics, no yellow marker wash. Full rules, tokens, and anti-patterns live in `references/kami-design.md`. The old brick-red / pale-yellow default is retired.

When to keep Kami: the default — especially when the user wants 高级感 / 文档感 / 克制 / 正式 / 专业. When to override the theme explicitly: the user asks for high-saturation, playful, or "小红书爆款" visual energy; then provide a custom `theme` in the spec, never by silently reverting the defaults.

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

For `mixed` or `image-led` specs, these are hard requirements:

- 每张图先写一句关系命题：这张图让读者比读段落更快看见的流程、对比、趋势或分层是什么（[references/diagram-system.md](references/diagram-system.md) 的一句话测试）。过不了测试就不画；
- 知识型 deck 优先至少 2 张图卡（diagram 计入），但以一句话测试为准：内容只撑得住 0–1 张真有教学增量的图时，宁缺毋滥，不要为凑配额补装饰图；
- 每张图必须有语义明确的 `alt` 与 schema 合法的 `role`，并在规划中承担 hero、evidence、annotate、contrast、echo 或 transition 之一，不能只负责装饰；
- [assets/diagrams/](assets/diagrams/) 模板是候选不是默认：先按内容关系决定结构，再从模板里选最接近的作起点改写；内容被迫适配模板节点数时，删除、合并或重排节点，保留关系本身。

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

Comprehension probes come first — each is blocking, with the same weight as overflow:

- whether the slide still carries mood or meaning when its explanatory copy is covered (遮文仍懂);
- whether every image and diagram adds a teaching increment: it makes a flow, comparison, trend, or layer visible faster than the paragraph would (教学增量，diagram 一句话测试);
- whether every image card has a visual anchor and first reading target visible within one second at 1× phone size.

Then structure and craft:

- title hierarchy and line breaks;
- no clipped or overlapping text;
- readable source labels and table cells;
- consistent margins, rules, card radii, and page numbers;
- restrained highlighting and accent usage;
- sequence-level density and rhythm;
- accurate author/footer text;
- absence of copied identity elements;
- semantic role, focal point, crop, and provenance of every image;
- whether the image adds a relationship or proof instead of repeating nearby text;
- whether every image is non-decorative and has a named semantic job;
- absence of generic AI visual clichés used only as decoration;
- coherence of paper, ink, grain, tape, shadow, or other material treatments;
- sequence-level image cadence: no accidental return to a wall of text after an image-led opening;
- semantic fit between each page and its recorded composition intent;
- meaningful variation from recent decks without random novelty;
- at least one deliberate moment of contrast or surprise that serves the argument.

Diagram budget conformance is suggested, not blocking: `references/diagram-system.md` 的复杂度预算（节点数、字号档、宽度档）是默认参考，内容关系需要时允许偏离，偏离要在 manifest 里写一句理由。理解失败永远优先于预算合规。

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
