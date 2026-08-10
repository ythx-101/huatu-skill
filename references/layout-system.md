# Bounded carousel layout system

Use this reference when styling or reviewing a deck. These values protect legibility and consistency; they do not replace the model's visual thesis.

## Canvas and safe area

- Canvas: 1080×1350 pixels, 4:5.
- Default outer padding: 88–96 px horizontally, 76–90 px at the top, 70–86 px at the bottom.
- Keep important content at least 84 px from the bottom edge.
- Default to a clear vertical flow. Break alignment only when the composition intent explains the reading benefit.

## Type hierarchy

| Role | Default size | Guidance |
| --- | ---: | --- |
| Main title | 58–68 px | 1–3 lines, serif, weight 500, 1.1–1.3 line height |
| Section heading | 36–42 px | Serif, weight 500, short label with a small brand bar or rule |
| Body | 29–34 px | Serif-led, 1.5–1.6 line height; shorten before shrinking |
| Table/card text | 24–29 px | Use compact density only for structured data |
| Source/footnote | 20–24 px | Maintain contrast; do not hide weak sourcing |
| Metric | 42–54 px | Accent (墨蓝) color, weight 500, one value per visual cell |

Preferred Chinese display stack for claims and display moments:

`TsangerJinKai02, Source Han Serif SC, Source Han Serif CN, Noto Serif CJK SC, Noto Serif SC, Songti SC, STSong, Georgia, serif`

Preferred body stack: same serif stack (`--sans` equals `--serif`, Kami single-serif page).

Preferred mono stack (page numbers, eyebrows, step labels, commands — must include CJK fallback):

`JetBrains Mono, SF Mono, Fira Code, Consolas, Monaco, Source Han Serif SC, Songti SC, monospace`

### Kami 排版模式（默认）

- 衬线标题层级：层级靠字号与留白，不靠加粗/多色；标题与主张默认 `font-weight: 500`（禁止衬线 700/800 伪粗）。
- 行高：标题 **1.1–1.3**；密集块 **1.4–1.45**；阅读正文 **1.5–1.55**（轮播容差 ±0.05，不得回到无规范的 1.7）。
- 字距：中文正文 0.3pt（约 0.012em@33px）；英文 body 0；tracking 只给短标签/overline/eyebrow。
- 章节标记：小号墨蓝短条或发丝规则 + eyebrow 文字，禁止星星/emoji 装饰图标。
- 引文：左规则或发丝框，**不斜体**。
- 强调 ≤ 5% 版面：墨蓝只点睛（数字/短标签/一条规则/CTA）。

## Color roles

- Paper (parchment): `#F5F4ED`
- Ink (near-black): `#141413`
- Muted ink (stone): `#6B6A64`
- Accent (brand / 墨蓝): `#1B365D`
- Highlight (brand-tint): `#EEF2F7`
- Card (ivory): `#FAF9F5`
- Rule / border: `#E8E6DC` / `#E5E3D8`
- Warn 例外（暖色唯一豁免）: 底 `#F0E0D8` / 字 `#8B4513`

Allow brand overrides while preserving contrast. Kami 默认：墨蓝用于数字/短标签/左规则/CTA；高亮用浅墨蓝 tint（`#EEF2F7`）做文字标记，不作为大面积 wash；全部灰阶保持暖调，禁止冷灰作默认。

## Component selection

- `metrics`: 2–4 comparable numbers.
- `compare`: two or three competing definitions, approaches, or roles.
- `table`: facts that require row/column scanning; keep to 3–5 columns.
- `steps`: stages, thresholds, or a maturity model.
- `quote`: one authoritative or provocative voice, with a source.
- `callout`: one decisive warning, implication, or takeaway.
- `chips`: short categories or reading promises, not sentences.
- `bullets`: 3–6 parallel facts; start each item with the information-bearing phrase.
- `image`: one local photograph, illustration, collage render, or texture-bearing scene with a declared semantic role. Prefer one strong image to several unrelated thumbnails.

## Image layout

- Recommended image block height: 320–620 px, depending on slide density.
- Use `cover` when crop is part of the composition; use `contain` for diagrams, cutouts, and authored illustrations.
- Set `position` to preserve the face, hand, object, or gesture that carries meaning.
- `paper` adds a restrained physical frame; `bleed` prioritizes scale; `cutout` preserves transparent objects; `monochrome` is for intentional one-color editorial treatment.
- A caption should add observation, provenance, or a second layer of meaning. Do not restate the title.
- Do not place body copy over a busy image unless contrast is measured and the composition specifically needs it.

## Composition archetypes and primitives

Archetypes are optional helpers, not finished templates:

- `editorial`: sustained reading and evidence;
- `poster`: promise, transition, metric, or resolution;
- `split`: contrast, before/after, or two-sided tension;
- `diagram`: system, mechanism, or spatial relationship;
- `timeline`: stages or change over time;
- `custom`: a justified content-specific composition.

Supported primitives are `scale-contrast`, `framing`, `alignment-break`, `annotation`, `flow`, `whitespace`, and `repetition`. Use no more than needed. Each primitive must have a semantic role; decorative accumulation is not diversity.

## Density

- `airy`: cover, transition, and conclusion; one or two blocks.
- `normal`: default; two to four blocks.
- `compact`: comparison and data pages only; structured blocks, not a wall of prose.

Shorten content before changing a page to compact. If a compact page still overflows, split it.

## Highlighting

Highlight only text that helps a scanning reader reconstruct the argument. Good candidates are a threshold, a contrast, a decision signal, or a consequence. Do not highlight complete paragraphs.

## Visual QA checklist

- Can the slide's message be understood in three seconds?
- Does the title state a claim rather than only a topic?
- Is the reading order unambiguous?
- Are data cells aligned and comparable?
- Are highlights sparse and meaningful?
- Are citations visually attached to the claims they support?
- Is the smallest text readable on a phone-sized preview?
- Does the footer avoid competing with the content?
- Does the slide look like the same deck without being mechanically identical?
- Does the visual form express the recorded composition intent?
- Is variation caused by the argument, not merely by a quota?
- Does any surprise clarify a turning point rather than distract from it?
- Does each image have an obvious semantic role and intentional crop?
- Does the sequence offer a perceptual pause, not only changes in card arrangement?
