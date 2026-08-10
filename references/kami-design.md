# Kami 设计法则（huatu 默认主题 v2.0）

> 来源：tw93 Kami 设计系统（`/tmp/kami`，CHEATSHEET / design.md / anti-patterns.md）。
> huatu v2.0 起 Kami **替换默认主题**：暖纸画布 + 墨蓝强调 + 衬线层级 + 克制美学。
> 用户显式 `theme` 覆盖仍然可用，但不改变出厂默认。

一句话：**暖纸画布、墨蓝强调、衬线承载层级，避免冷灰与硬阴影**。
不是 UI 框架，而是一套约束系统，让页面稳定、清晰、可读。

---

## 一、十大不变量（每条都有代价，覆盖前先想清楚）

| # | 不变量 | 轮播适配（1080×1350） |
| --- | --- | --- |
| 1 | 画布暖纸 `#f5f4ed`，绝不纯白 | `theme.background` 默认 `#F5F4ED`；禁止 `#fff` / `#ffffff` |
| 2 | 单强调色：墨蓝 `#1B365D`，无第二彩色 | `theme.accent` 默认 `#1B365D`；强调仅用于数字/短标签/左规则/CTA |
| 3 | 全部灰阶暖调（黄棕 undertone），无冷蓝灰 | `muted`/边框/卡片均带暖调；冷灰（`#6b7280`、`#9ca3af`、`#f3f4f6` 等）禁止作默认 |
| 4 | 衬线承载层级：中文标题衬线、正文以衬线为主 | 标题/主张/章节 = 衬线栈；无衬线仅限页码/极小标签/命令等 UI chrome |
| 5 | 衬线字重锁 **500**，无伪粗 | 标题/主张默认 `font-weight: 500`；禁止衬线 `700/800` 作默认 |
| 6 | 行高规范 | 标题 **1.1–1.3**；密集块 **1.4–1.45**；阅读正文 **1.5–1.55**（轮播容差 ±0.05） |
| 7 | 字距克制 | 中文正文 `0.3pt`（≈0.012em@33px）；英文 body 0；tracking 只给短标签/overline |
| 8 | 标签/底色用 **solid hex** tint | 优先固色 tint（`#EEF2F7` / `#E4ECF5`），避免依赖半透明叠色 |
| 9 | 无硬阴影 | 深度只允许 ring / whisper（极轻 `box-shadow` 或发丝边框）；禁止硬偏移色块阴影 |
| 10 | 无斜体默认 | 模板与默认 demo 不用 italic 装饰整段；引文用左规则而非斜体 |

## 二、色板 tokens（默认 theme / 模板根变量唯一来源）

| Token 角色 | 规范值 | 用途 | 禁止 |
| --- | --- | --- | --- |
| parchment / background | `#F5F4ED` | 画布背景 | 纯白 `#ffffff`、旧默认 `#F4EFE4` |
| brand / accent | `#1B365D` | 唯一强调色：数字、标签、左规则、CTA | 旧砖红 `#A23F32` |
| near-black / ink | `#141413` | 主文 | 冷灰黑 `#111827` 等 |
| stone / muted | `#6B6A64` | 三级文字 / metadata | 冷灰 `#6b7280`、`#9ca3af` |
| ivory / card | `#FAF9F5` | 抬升容器 | 冷白卡片 |
| border / rule | `#E8E6DC` / `#E5E3D8` | 发丝分割线、卡片边 | 冷色 border |
| brand-tint / highlight | `#EEF2F7` / `#E4ECF5` | 标签底、轻强调、文字标记 | 黄荧光 `#F3E58B` |
| breaking（唯一暖色例外） | 底 `#F0E0D8` / 字 `#8B4513` | 警告 callout（暖桃/暖棕） | 黄系警告 wash |
| dark-surface | `#30302E` / `#141413` | dark callout / quote | 冷 slate |

暖灰判定口诀：暖灰在 `rgb()` 中 **R ≈ G > B**（或 R > G > B 小差）；冷灰是 **R < G < B** 或 R = G = B。

衬线字体栈（中文优先）：

`TsangerJinKai02 → Source Han Serif SC → Source Han Serif CN → Noto Serif CJK SC → Noto Serif SC → Songti SC → STSong → Georgia → serif`

等宽栈（命令/页码/标签，须含 CJK fallback 防缺字）：

`JetBrains Mono → SF Mono → Fira Code → Consolas → Monaco → Source Han Serif SC → Songti SC → monospace`

## 三、反模式清单（文档 + 实现双重约束）

### 视觉反模式（BLOCKING 级）
- **C1 强调色语言过多**：每页强调语义 ≤ 3 处（数字/短标签/一条规则）；全 deck 只允许墨蓝一个品牌色。
- **C2 装饰图标做章节标记**：章节靠衬线标题 + 短规则/eyebrow 文字；禁止星星/emoji/无语义 clip-art 当章节符号。
- **C3 图表无洞察**：`table` / `metrics` / 数据块必须配洞察句（标题或 callout 说「意味着什么」），禁止裸表。
- **C4 硬阴影 / 立体假深度**：禁止硬偏移色块阴影（如 `-8px 8px 0`）与重投影；只允许 ring / whisper。
- **C5 冷灰 UI**：见色板表；默认 token 一律暖调。
- **C6 黄荧光笔大 wash**：默认 theme 与 `callout.warn` 不得以黄系为默认警告语言；警告用暖桃/暖棕（`#F0E0D8` / `#8B4513`）或墨蓝 tint。
- **C7 每页相同卡片堆叠**：6+ 页 deck 不得同一 block signature；保持 composition 多样性。

### 内容反模式（沿用 Kami anti-patterns，写作时对照）
- 形容词堆砌无数字 → 给数字；开头段废话 → 删；标题标签化 → 主张句。
- 编造指标精度 → 对齐来源精度；图表与文字矛盾 → 统一。
- 装饰性图表复述正文 → 图表必须加一个维度（对比/趋势/分布）。
- AI 腔（赋能/一站式/破折号堆叠）→ 说人话。

## 四、轮播适配要点（Kami → 1080×1350）

- **强调 ≤ 5% 版面**：墨蓝只点睛；单页 accent/highlight 面积比建议 ≤ 0.05（渲染器 `qa.json` 有 `highlightAreaRatio` 参考）。
- **字重 500**：衬线标题默认 500；层级靠字号与留白，不靠加粗/多色。
- **无硬阴影**：卡片由 ivory 填充 + 发丝边框承托（`#E5E3D8`），不靠投影；柔影仅 `rgba(20,19,19,.06)` 量级。
- **发丝分割**：用 `#E5E3D8` 1–1.5px 边框替代重边框。
- **单衬线页面**：`--sans` 恒等于 `--serif`；等宽仅用于页码/eyebrow/step 标签/命令。
- **引文**：左规则或发丝框，不斜体。
- **何时用**：Kami 是默认风格；用户要「高级感/文档感/克制/正式/专业」时保持；只有用户明确要「高饱和/活泼/小红书爆款视觉」时才显式覆盖 theme。
