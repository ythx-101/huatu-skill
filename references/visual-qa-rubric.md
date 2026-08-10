# Visual QA rubric

Use the rubric after static QA. Score each dimension from 1 to 5 and cite visible evidence. A total score does not override a blocking defect.

## Page dimensions

- **Semantic fit:** the form makes the page's relationship easier to understand.
- **Hierarchy:** the first, second, and third reading targets are unambiguous.
- **Balance:** density and whitespace feel intentional at phone-preview size.
- **Restraint:** highlights, borders, motifs, and effects do not compete.
- **Craft:** line breaks, alignment, typography, and details feel resolved.
- **Image purpose:** the visual anchor carries meaning rather than decorating a finished text layout.
- **Image-text relation:** copy annotates, contrasts, echoes, documents, or advances the image without repeating it.
- **Material coherence:** texture, grain, tape, shadow, and handmade traces form a restrained system.

## Deck dimensions

- **Narrative rhythm:** density and energy change with the argument.
- **Coherence:** pages belong together without becoming identical.
- **Conceptual novelty:** the direction differs meaningfully from recent work.
- **Deliberate surprise:** at least one turn is memorable because it clarifies meaning.
- **Platform fit:** the deck can be scanned quickly without reducing it to generic social cards.
- **Perceptual cadence:** image-led, structural, dense, and quiet pages alternate with intention.

## Kami 模式专项（默认主题 v2.0，逐页核对）

- **Accent 克制（C1/B2）**：墨蓝只点睛；每页强调语义 ≤ 3 处；单页 accent/highlight 面积比参考 ≤ 0.05（对照 `qa.json` 的 `highlightAreaRatio`）；全 deck 无第二品牌强调色。
- **暖灰（C5/B3）**：muted / border / card 均带黄棕 undertone；出现 `R < G < B` 或 `R = G = B` 的灰即记为冷灰缺陷；`#6b7280` / `#9ca3af` / `#f3f4f6` 家族直接标红。
- **衬线层级（B4/A2）**：标题/主张/章节为衬线；正文以衬线为主；无衬线仅限页码/极小标签/命令。
- **字重与行高（B5/B6）**：衬线标题默认 500（禁止 700/800 伪粗）；标题行高 1.1–1.3、密集 1.4–1.45、阅读 1.5–1.55（±0.05）。
- **阴影类型（B9/C4）**：只允许 ring / whisper；出现硬偏移色块阴影（如 `-8px 8px 0`）或重投影即 BLOCKING。
- **无斜体（B10）**：模板/默认 demo 无 italic 整段装饰。
- **反模式扫一眼（C1–C6）**：无装饰图标章节标；数据块带洞察句；无黄荧光 wash；无硬阴影；无冷灰条；无每页同构卡片。
- **数据洞察（C3）**：凡 `table` / `metrics` 页面，标题或 callout 必须说明「意味着什么」。

## Review contract

Return:

`VERDICT: PASS | NEEDS_CHANGES | BLOCKED`

`BLOCKING: required fixes or none`

`SUGGESTED: non-blocking improvements or none`

`EVIDENCE: page numbers, visible regions, QA codes, and manifest claims checked`

For any deck using images, also report:

`ASSET_EVIDENCE: source class, semantic role, focal point, crop, treatment, and whether attribution is required`

For candidate selection, compare A/B twice with order swapped. Reject a judgment when the preferred candidate changes only because of order or when the reviewer cannot cite visible evidence.
