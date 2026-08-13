# Diagram SVG templates

这里提供 6 个 1080 宽、自包含的 SVG 起点，用于 huatu 的 `mixed` / `image-led` 轮播。它们只规定关系语法和视觉预算，不规定真实内容。

## 用法

1. 复制最接近内容关系的模板到 carousel spec 所在项目的本地素材目录。
2. 只改 `<!-- DATA START -->` 与 `<!-- DATA END -->` 之间的中文占位文字、节点和连线；修改后仍须遵守 `references/diagram-system.md`。
3. 保持 `viewBox` 宽 1080，节点不超过 9 个，焦点不超过 2 个。
4. 在 carousel spec 中增加 `image` 块，让 `src` 指向复制后的 SVG。

推荐的 image 块：

```json
{
  "type": "image",
  "src": "assets/diagram.svg",
  "alt": "从输入经过判断分支并回到下一轮的流程示意图",
  "role": "evidence",
  "fit": "contain",
  "position": "center",
  "treatment": "paper",
  "height": 520
}
```

## 与 spec-format.md 的对应关系

| image 字段 | 模板建议 |
| --- | --- |
| `src` | 本地相对或绝对 SVG 路径；远端 URL 不可用 |
| `alt` | 描述关系与结论，不要只写“流程图” |
| `role` | 机制主体用 `hero`；支撑论点通常用 `evidence`；跨页复现的结构线索用 `motif` |
| `fit` | 默认 `contain`，避免裁掉轴、箭头或标签 |
| `position` | 默认 `center`；只有构图明确偏置时才改 |
| `treatment` | 默认 `paper`；需要与页面完全融合时用 `plain`；diagram 不建议 `bleed` 或 `cutout` |
| `height` | 通常 460–620；以手机端可读和页面留白为准，合法范围仍是 240–700 |

## 模板选择

- `flowchart.svg`：判断、分支、合流与回环。
- `steps-flow.svg`：一条横向的固定步骤链。
- `architecture-layer.svg`：纵向层级和跨层依赖。
- `timeline.svg`：时间轴上的里程碑与转折。
- `quadrant.svg`：两个轴共同决定的位置。
- `split-compare.svg`：两种方案在相同维度下逐项对照。

## 禁忌

- 不改色板，不添加第二强调色，不用渐变或 `rgba()` 填充。
- 不新增节点宽度档；只用 128 / 144 / 160，节点高度只用 32 / 64。
- 不用真实用户内容、姓名、账号、指标或项目数据作为模板占位。
- 不复制外部模板的文案、水印、署名或身份元素。
- 不为塞入长句缩小字号；先删字、拆节点或拆成两张图。
- 不把图当背景装饰；若图没有增加流程、对比、趋势或分层，改用正文。
