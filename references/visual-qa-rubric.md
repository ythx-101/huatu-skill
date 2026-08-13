# Visual QA rubric

Use the rubric after static QA. Score each dimension from 1 to 5 and cite visible evidence. A total score does not override a blocking defect.

## Comprehension gates（先于打分，一票否决）

评分前先过三道理解探针，任一失败 → `VERDICT: BLOCKED`（与溢出/裁剪同级，不得用总分折中）：

- **遮文仍懂**：遮住页面解释性文字后，页面是否仍传达关系、机制或判断？失败 = 排版只是装饰。
- **教学增量**：每张图/表是否让读者比读段落更快看见方向、差异、先后或层级（diagram 一句话测试）？失败 = 删图或重构，不许「为了填模板而画」。
- **1× 可见入口**：手机 1× 下，读者一秒内能否看见入口、焦点与阅读方向？失败 = 重排层级或放大关键元素。

**Semantic fit 是一票否决探针，不是普通打分维度**：任何一页无法说清「这页排版帮读者先看见什么关系」（对照 manifest 的 `compositionIntent`），即 `NEEDS_CHANGES`。评分只描述程度，不能替代这层判断。

一句话钉死：遮文 / 教学增量 / 1× 入口任一失败 = `BLOCKED`；仅 `compositionIntent` 对不上但遮文仍懂 = `NEEDS_CHANGES`（改 manifest 或重排，不必推翻全 deck）。

## Page dimensions

- **Semantic fit:** the form makes the page's relationship easier to understand（一票否决探针，见上）。
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

`BLOCKING: required fixes or none`（理解探针失败、溢出、裁剪、遮挡一律计入 BLOCKING）

`SUGGESTED: non-blocking improvements or none`

`EVIDENCE: page numbers, visible regions, QA codes, and manifest claims checked`

For reference-driven or image-led decks, also report:

`THESIS_EVIDENCE:` 逐页：本页关系命题（manifest `compositionIntent` 声称的关系）+ 版面证据（哪个视觉元素让该关系可见）。说不出的页面即未通过 Semantic fit 探针。

For any deck using images, also report:

`ASSET_EVIDENCE: source class, semantic role, focal point, crop, treatment, and whether attribution is required`

For candidate selection, compare A/B twice with order swapped. Reject a judgment when the preferred candidate changes only because of order or when the reviewer cannot cite visible evidence.
