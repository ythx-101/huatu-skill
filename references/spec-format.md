# Carousel JSON format

The renderer accepts UTF-8 JSON. All user-visible values are plain text.

## Top level

```json
{
  "title": "Internal deck label",
  "author": "@your-name",
  "referenceDriven": true,
  "designManifest": {},
  "theme": {
    "background": "#F4EFE4",
    "ink": "#171714",
    "muted": "#5F5C55",
    "accent": "#A23F32",
    "highlight": "#F3E58B",
    "card": "#FBF8F0"
  },
  "slides": []
}
```

`slides` is required. The renderer supports 1–12 slides; 6–10 is the editorial recommendation, not a platform limit.

`referenceDriven` defaults to `false` for backward compatibility. When it is `true`, `designManifest` and a `composition` object on every slide are required. The renderer writes the manifest beside the exported images and never marks it visually approved.

## Design manifest

```json
{
  "candidateDirection": "Diagram-spatial",
  "visualThesis": "The workflow is a relay of decisions and evidence.",
  "readerEmotion": "Complexity, orientation, then control.",
  "semanticMetaphor": "A relay circuit with human-controlled gates.",
  "motifs": ["gate", "handoff"],
  "rhythmPlan": "Alternate system maps with decisive checkpoints.",
  "compositionIntent": ["The eye sees the gate before the details."],
  "contrastPlan": "Compress the system before each human decision.",
  "typeStrategy": "Neutral sans body with monospaced operational labels.",
  "avoidList": ["uniform stacked cards", "highlight on every paragraph"],
  "whyThisVisual": "Spatial flow makes a multi-step process easier to understand."
}
```

`compositionIntent` must contain exactly one non-empty sentence per slide. `motifs` contains one or two entries. Keep the manifest concise and safe to show to a human reviewer.

For mixed or image-led work, the manifest may also include:

```json
{
  "visualMode": "mixed",
  "materialSystem": ["paper fiber", "pencil annotation"],
  "imageCadence": "Image-led promise, structural explanation, quiet transition, evidence, then resolution.",
  "assetPlan": [
    {
      "slide": 1,
      "role": "hero",
      "sourceClass": "original illustration",
      "focalPoint": "walking figure inside a returning line",
      "textImageRelationship": "embody"
    }
  ]
}
```

`visualMode` is `editorial`, `mixed`, `image-led`, `photo-diary`, `object-study`, or `poetic-poster`. These fields guide model judgment and independent review; they are not an excuse for a weak visible result.

## Slide

```json
{
  "eyebrow": "Optional small label",
  "title": "Required slide claim",
  "density": "normal",
  "composition": {
    "archetype": "diagram",
    "primitives": ["flow", "annotation"],
    "intent": "The eye follows evidence into the decision gate."
  },
  "blocks": [],
  "footer": "Optional footer override"
}
```

`density` is `airy`, `normal`, or `compact`.

`composition.archetype` is `editorial`, `poster`, `split`, `diagram`, `timeline`, or `custom`. Supported primitives are `scale-contrast`, `framing`, `alignment-break`, `annotation`, `flow`, `whitespace`, and `repetition`. A `custom` composition also requires a non-empty `reason`.

## Common rich-text fields

Blocks that contain `text` or list items may include:

```json
{
  "text": "A decision signal is more useful than a slogan.",
  "emphasis": ["decision signal"]
}
```

Each emphasis string must occur literally in the text. Emphasis remains text and cannot contain HTML.

## Block types

### heading

```json
{"type":"heading","text":"Why this matters"}
```

### paragraph

```json
{"type":"paragraph","text":"One concise paragraph.","emphasis":["concise"]}
```

### metrics

```json
{
  "type":"metrics",
  "columns":3,
  "items":[
    {"value":"3×","label":"faster review","source":"Internal test"}
  ]
}
```

### bullets

```json
{
  "type":"bullets",
  "items":[
    {"text":"Lead with the decision.","emphasis":["decision"]},
    "Keep each item parallel."
  ]
}
```

### quote

```json
{"type":"quote","text":"One strong sentence.","source":"Source name","variant":"light"}
```

`variant` is `light` or `dark`.

### compare

```json
{
  "type":"compare",
  "items":[
    {"title":"Option A","subtitle":"Best for speed","items":["Low setup","Less control"]},
    {"title":"Option B","subtitle":"Best for depth","items":["More setup","More control"]}
  ]
}
```

### table

```json
{
  "type":"table",
  "headers":["Dimension","A","B"],
  "rows":[["Cycle","Days","Weeks"],["Output","Draft","System"]]
}
```

Keep every row the same length as `headers`.

### steps

```json
{
  "type":"steps",
  "items":[
    {"label":"Stage 1","title":"Make individuals faster","text":"Learn the workflow."},
    {"label":"Stage 2","title":"Redesign the system","text":"Change handoffs and permissions."}
  ]
}
```

### callout

```json
{"type":"callout","title":"Decision signal","text":"Two teams built conflicting systems.","variant":"warn"}
```

`variant` is `plain`, `warn`, `accent`, or `dark`.

### chips

```json
{"type":"chips","items":["Evidence","Decision","Action"]}
```

### image

```json
{
  "type": "image",
  "src": "assets/loop-thread.png",
  "alt": "A red thread returns through five observation points",
  "caption": "The line returns with evidence, not to the same state.",
  "role": "hero",
  "fit": "contain",
  "position": "center",
  "treatment": "paper",
  "height": 500
}
```

- `src` is a local PNG, JPEG, WebP, or SVG path, absolute or relative to the JSON spec. Remote URLs are rejected.
- `alt` and `role` are required. `role` is `hero`, `evidence`, `atmosphere`, `texture`, `motif`, or `transition`.
- `fit` is `cover` or `contain`; `position` is `center`, `top`, `bottom`, `left`, or `right`.
- `treatment` is `plain`, `paper`, `bleed`, `cutout`, or `monochrome`.
- `height` is an integer from 240 to 700 pixels.

## Output behavior

The renderer rejects unknown block types, malformed tables, excessive emphasis, invalid interpreted manifests, unsupported composition values, and inaccessible interpreted themes. Automated QA fails when content exceeds a slide's safe content region. Fix overflow by editing, splitting, or changing components; do not hide it with CSS.

`qa.json` separates `structurally_valid`, `veg_review_required`, and `visually_approved`. The last value is always `false`; only the human may grant visual approval after inspecting the deck.

For interpreted decks, the renderer appends a hashed, non-sensitive fingerprint to `design-history.jsonl` beside the spec and warns when the new direction closely repeats one of the latest five entries. Use `--no-history` for test fixtures.
