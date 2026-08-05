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
| Main title | 58–68 px | 1–3 lines, strong serif, 1.12–1.22 line height |
| Section heading | 36–42 px | Short label with a small rule or star marker |
| Body | 29–34 px | 1.5–1.7 line height; shorten before shrinking |
| Table/card text | 24–29 px | Use compact density only for structured data |
| Source/footnote | 20–24 px | Maintain contrast; do not hide weak sourcing |
| Metric | 42–54 px | Accent color, one value per visual cell |

Preferred Chinese display stack for claims and display moments:

`Songti SC, STSong, Noto Serif CJK SC, Source Han Serif SC, serif`

Preferred body and label stack:

`PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif`

## Color roles

- Paper: `#F4EFE4`
- Ink: `#171714`
- Muted ink: `#5F5C55`
- Accent: `#A23F32`
- Highlight: `#F3E58B`
- Card: `#FBF8F0`
- Rule: `#25221E`

Allow brand overrides while preserving contrast. Use accent red primarily for numbers and tiny labels. Use yellow as a text marker, not as a large background wash.

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
