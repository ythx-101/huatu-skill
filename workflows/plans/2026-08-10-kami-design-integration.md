# 计划：huatu-skill 融合 Kami 设计系统（迭代 v2.0）

**日期**: 2026-08-10
**状态**: implemented（2026-08-11 已实施并提交 v2.0）
**任务定级**: medium（skill 文档 + 渲染系统改进，有回归测试）
**仓库**: ~/.codex/skills/huatu-skill（已 git init）

## 1. 目标
把 tw93 的 Kami 设计系统（暖纸 + 墨蓝 + 衬线层级 + 克制美学）融入 huatu-skill，提升轮播图设计质量。保留 huatu-skill 的内容蓝图/证据规则/视觉QA 优势，吸收 Kami 的设计克制。

## 2. 现状证据
- huatu-skill：内容蓝图 + 8步流程 + 视觉QA（1080×1350 轮播图专精）
- Kami（/tmp/kami）：设计 tokens + 十大设计法则 + 反模式清单
- 已实测：Kami 风格重做 Herdr 轮播图，墨蓝克制（0.05-0.36%），比原版更安静高级

## 3. 设计（融入内容）
### 3.1 新增 references/kami-design.md（Kami 设计法则参考）
- 十条设计不变量（暖纸/单强调色/暖灰/衬线层级/字重锁500/行高/字距/柔阴影/无斜体）
- 反模式清单（强调色≤3/图表带洞察/无装饰图标/无硬阴影）
- 色板 tokens（parchment #f5f4ed / ink-blue #1B365D 等）

### 3.2 更新 references/design-contract.md
- 新增 "Kami 风格" 可选项（用户请求时用暖纸+墨蓝+衬线）
- 硬性下限增加：单强调色（Kami 模式）、暖灰、柔阴影
- 审查警告增加：强调色>3、硬阴影、冷灰

### 3.3 更新 references/layout-system.md
- 新增 Kami 排版模式：衬线标题层级、行高规范（1.1-1.3/1.4-1.45）、字距规范
- 保留现有小红书爆款模式作为默认

### 3.4 更新 SKILL.md
- 提及 Kami 风格选项 + 何时使用（用户要"高级感/文档感/克制"时）

### 3.5 更新 visual-qa-rubric.md
- 增加 Kami 风格 QA：强调色用量、阴影类型、冷灰检测

## 4. 测试
- 用 Kami 风格重做一张测试轮播图（Herdr 内容），验证渲染
- 回归：默认爆款风格不受影响
- 视觉 QA 通过（无溢出/密度安全）

## 5. 回滚
- git 版本控制，可 revert
- 新增文件独立，不影响现有流程

## 6. Roster
- orchestrator: pi
- sole-writer: codex
- reviewer: grok（跨厂商）

## 7. 需要人类决策
- [ ] 批准计划
- [x] 已确认：Kami 风格直接替换默认（2026-08-10 用户批准）
