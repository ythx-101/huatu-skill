# Design contract

## Hard floors

- 1080×1350 canvas unless the user explicitly requests another supported target.
- No overflow, clipping, unsafe executable markup, or missing required content.
- Body and source text contrast at least 4.5:1 in reference-driven work; large display text at least 3:1.
- No more than three emphasis phrases per slide.
- Do not copy another creator's watermark, avatar, account name, signature, or distinctive identity treatment.
- Facts, quotations, and sources remain unchanged unless the user authorizes editorial revision.
- Local image assets must be PNG, JPEG, WebP, or SVG. Remote URLs, scripts, and HTML payloads are not image sources.
- Benchmark images may be studied but not shipped as output unless the user owns or licenses them and explicitly provides them for reuse.

## Review warnings

- occupied content below 48% or above 94% for normal/compact pages;
- occupied content below 30% or above 88% for airy pages;
- more than half the deck repeats one block signature;
- a six-plus-slide deck uses only one composition family;
- a new direction strongly resembles a recent local visual fingerprint.
- an image-led manifest renders without a meaningful image block;
- a mixed or image-led deck opens visually but then falls back into three or more consecutive text-first pages;
- an image has no stated semantic role or its crop hides the intended focal point.

Warnings require visual review, not automatic rejection. Intentional whitespace and purposeful repetition are valid when the manifest and visible result support them.

## Creative freedom

Inside the hard floors, the model may combine composition primitives, change archetypes page by page, or use `custom`. The composition intent must explain the choice. Rules may not be added merely because they are easy to measure.
