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

### 默认主题：Kami（v2.0 起，见 `references/kami-design.md`）

- 默认 tokens：暖纸 `#F5F4ED` 画布 + 墨蓝 `#1B365D` 单强调色 + 暖灰体系（近黑 `#141413` / 石色 `#6B6A64` / 象牙 `#FAF9F5` / 边框 `#E8E6DC`）。旧「纸红 `#A23F32` / 黄荧光 `#F3E58B`」默认退役。
- **单强调色**：全 deck 只允许墨蓝一个品牌强调色；强调语义每页 ≤ 3 处，墨蓝版面占比 ≤ 5%。
- **暖灰**：muted / border / card 均带黄棕 undertone；冷灰（`#6b7280`、`#9ca3af`、`#f3f4f6`、`#111827` 等）不得作默认 token。
- **衬线标题**：标题/主张/章节必须衬线（TsangerJinKai02 → Source Han Serif SC → Songti SC → serif）；无衬线仅限页码/极小标签/命令等 UI chrome。
- **字重 500**：衬线标题默认 `font-weight: 500`，禁止衬线 700/800 伪粗作默认。
- **行高规范**：标题 1.1–1.3；密集块 1.4–1.45；阅读正文 1.5–1.55（轮播容差 ±0.05）。
- **无硬阴影**：深度只允许 ring / whisper（极轻 shadow 或发丝边框）；禁止硬偏移色块阴影与重投影。
- **无斜体默认**：不用 italic 装饰整段；引文用左规则/发丝框。
- 用户显式 `theme` 覆盖仍可用，但不改变出厂默认。

## Review warnings

- occupied content below 48% or above 94% for normal/compact pages;
- occupied content below 30% or above 88% for airy pages;
- more than half the deck repeats one block signature;
- a six-plus-slide deck uses only one composition family;
- a new direction strongly resembles a recent local visual fingerprint.
- an image-led manifest renders without a meaningful image block;
- a mixed or image-led deck opens visually but then falls back into three or more consecutive text-first pages;
- an image has no stated semantic role or its crop hides the intended focal point.
- **强调色过曝**：单页 accent/highlight 面积比明显偏离克制（参考 ≤ 0.05），或每页强调语义 > 3 处，或出现第二个品牌强调色。
- **硬阴影残留**：检测到硬偏移色块阴影 / 重投影（Kami 只允许 ring / whisper）。
- **冷灰检测**：默认 tokens 之外出现冷灰（`R < G < B` 或 `R = G = B` 的灰），或 `#6b7280` / `#9ca3af` / `#f3f4f6` 家族。
- **黄荧光残留**：默认 theme / `callout.warn` 出现黄系警告 wash（应使用暖桃 `#F0E0D8`/`#8B4513` 或墨蓝 tint）。

Warnings require visual review, not automatic rejection. Intentional whitespace and purposeful repetition are valid when the manifest and visible result support them.

## Creative freedom

Inside the hard floors, the model may combine composition primitives, change archetypes page by page, or use `custom`. The composition intent must explain the choice. Rules may not be added merely because they are easy to measure.
