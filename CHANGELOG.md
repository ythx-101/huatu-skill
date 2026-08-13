# Changelog

## [2.1.0] - 2026-08-12

### 新增
- 新增 6 种可复用 diagram SVG 模板与配套表示意规范，覆盖流程、步骤、架构分层、时间线、象限和双栏对比。
- 新增 mixed diagram 示例与模板结构回归测试。

### 变更
- 恢复 image-led 图文结合：知识型、机制型和研究型内容默认使用 `mixed` 图文交替路径，强化视觉锚点、语义角色与图卡 QA 引导。

## [2.0.0] - 2026-08-11

### 新增
- Kami 设计系统替换默认主题：暖纸 `#F5F4ED` + 墨蓝 `#1B365D` 单强调色 + 暖灰体系（近黑 `#141413` / 石色 `#6B6A64` / 象牙 `#FAF9F5` / 边框 `#E8E6DC`）+ 衬线层级（字重锁 500）+ 克制强调 ≤5% 版面。
- 新增 `references/kami-design.md`：十大设计不变量、色板 tokens 表、反模式清单（C1–C7）、1080×1350 轮播适配说明。
- 模板 Kami 化：单衬线页面（`--sans = --serif`，TsangerJinKai02 优先）、无硬阴影（仅 whisper）、无默认斜体、章节星标改墨蓝短条、`callout.warn` 改暖桃/暖棕（`#F0E0D8` / `#8B4513`）、卡片改 ivory 填充 + 发丝边框。
- 新增默认主题回归测试 `test_default_theme_is_kami`。

### 变更
- 旧「纸红 `#A23F32` / 黄荧光 `#F3E58B`」默认退役。
- `references/design-contract.md`、`references/layout-system.md`、`references/visual-qa-rubric.md`、`SKILL.md`、`references/spec-format.md` 同步 Kami 默认与 QA 维度（强调色过曝 / 硬阴影 / 冷灰 / 黄荧光残留检测）。
- 行高规范：标题 1.1–1.3、密集块 1.4–1.45、阅读正文 1.5–1.55（±0.05）；中文正文字距 0.3pt。

### 移除
- 模板中的硬偏移色块阴影（`-8px 8px 0`）、黄系警告 wash、装饰图标章节标记（`☆`）、默认 italic 引文。

## [1.0.0] - 2026-08-05

- 初始发布（Rednote Canvas → Huatu Skill 基线）：内容蓝图 + 8 步流程 + 1080×1350 确定性渲染 + 视觉 QA 合约（`VERDICT / BLOCKING / SUGGESTED / EVIDENCE`）。
