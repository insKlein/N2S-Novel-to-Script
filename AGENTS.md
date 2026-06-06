# N2S Agent Operating Guide

N2S 是一个小说转结构化剧本工具。所有 Agent 只服务于“小说文本 -> YAML 剧本初稿”，不产出图片、视频或制作环节内容。

## 流程

```text
~analyze      -> novel-analyzer + insight-architect
~plan         -> episode-architect + emotion-architect
~write N      -> script-writer + visual-storyteller + continuity-recorder
~review N     -> script-comparator + review-director
~final-check  -> 文件完整性、称呼、越界字段检查
```

## 分层

- `agents/`：定义角色和职责。
- `skills/`：定义执行步骤和检查清单。
- `references/`：定义稳定标准和方法论。
- `scripts/`：提供 CLI、模型调用、YAML 写出和校验。

## 约束

- 输入小说至少 3 个章节或段落块。
- 核心剧本产物必须是 `outputs/{剧本名}/scripts/ep<N>.yaml`。
- YAML 结构必须符合 `docs/yaml-schema.md`。
- `camera_note` 只允许基础景别：特写、近景、中景、全景、远景。
- 禁止输出图片、视频、导演制作环节字段。
