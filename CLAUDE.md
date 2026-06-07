# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**AI 小说转剧本工具（N2S: Novel-to-Script）** — 将 3 章节以上中文网络小说自动转换为结构化剧本（YAML 格式），降低改编门槛，让作者快速获得可编辑、可进一步打磨的剧本初稿。

目标仓库：https://github.com/Liu-YuChen0906/N2S-Novel-to-Script

## 参考项目

`novel-to-script-team/` 是本项目的参考/灵感来源。它是一个多 Agent 协作的小说→短剧全流程生产系统（MIT 开源）。完整筛选分析见 `zmq/novel-to-script-team-分析文档.md`。

**核心差异**：
- 参考项目覆盖"小说→剧本→分镜→视频"全链路
- 本项目只做"小说→剧本"，**删除所有视频/分镜/图片生成内容**
- 参考项目输出 Markdown 剧本，**本项目输出 YAML 结构化剧本**

## 架构设计

### 四层架构

```
用户命令 (~analyze, ~write N 等)
  → Agent 层 (10 个专业角色，阶段负责人)
    → Skill 层 (12 个执行规则，定义步骤和产出格式)
      → Reference 层 (13 个方法论和标准)
        → Script 层 (5 个自动化工具脚本)
          → outputs/{剧本名}/ (阶段产物、审核记录、状态文件)
```

### 核心流水线（4+1 阶段）

```
阶段1: ~analyze  → novel-analyzer → insight-architect → genre-classifier → review-director
                   产出: 清洗文本、分析报告、角色档案、洞察报告、细粒度题材分类

阶段2: ~plan     → episode-architect → emotion-architect → review-director
                   产出: 分集目录、项目进度、情绪曲线

阶段3: ~write N  → script-writer → visual-storyteller → review-director → continuity-recorder
                   产出: 第N集剧本 (YAML)、风格分析、视觉叙事报告

阶段4: ~review N → script-comparator → review-director
                   产出: 逐一对比分析、综合审核报告

阶段6: ~final-check → UTF-8检查、称呼一致性、文件完整性
```

每阶段执行 **生成→审核→回改→复审→PASS** 循环，关键阶段双重审核（业务审核+合规审核）。

### 保留的 11 个 Agent

| Agent | 阶段 | 职责 |
|-------|------|------|
| `knowledge-curator` | 0 | 知识库维护、参考剧本管理 |
| `novel-analyzer` | 1 | 文本清洗、性别频判定、冲突建模、角色档案 |
| `insight-architect` | 1 | "开天眼"方法论、揭示隐藏真相、设计核心冲突 |
| `genre-classifier` | 1 | **🆕 细粒度题材分类**：基于起点分类体系精确到子类，匹配改编注意事项，不确定时询问用户 |
| `episode-architect` | 2 | 分集目录、情绪曲线、卡点设计 |
| `emotion-architect` | 2 | 情绪曲线、心理预期管理、认知负荷控制 |
| `script-writer` | 3 | **核心**：单集剧本创作(YAML)、参考剧本检索、风格自分析 |
| `visual-storyteller` | 3 | Show Don't Tell 执行、情绪→动作翻译 |
| `review-director` | 1-4 | 业务审核+合规审核双审、PASS/FAIL 判定 |
| `script-comparator` | 4 | 与 Top5 爆款剧本逐一对比（100分制） |
| `continuity-recorder` | 3+ | 跨集一致性跟踪、项目记忆维护 |

## 关键设计决策

### 可拍性 vs 分镜的边界（三层模型）

| 层 | 内容 | 决策 |
|----|------|------|
| 可拍性基本功 | 用动作/表情/道具替代心理描写 | **强制保留** |
| 编剧镜头意识 | 基础景别提示（特写/近景/中景/全景/远景） | **可选保留**（YAML `camera_note` 字段） |
| 导演分镜 | 运镜方案、九宫格、转场手法 | **完全删除** |

判断标准：**"这个信息是写给演员/摄影看的，还是写给剪辑/后期看的？"**

## 剧本输出格式

剧本以 **YAML** 格式输出，Schema 详见 `zmq/novel-to-script-team-分析文档.md` 第 11 章。

核心结构：
```yaml
meta: { script_title, source_novel, total_episodes, ... }
adaptation_summary: { genre, sub_genre, genre_detail: {...}, core_conflict, main_characters, ... }
naming_conventions: [...]
episodes:
  - episode_number: 1
    episode_meta: { duration, scene_count, emotion_peak, hook_type }
    scenes:
      - scene_id: 1
        location: { time, place, environment, lighting }
        emotion: "绝望→震惊"
        elements:
          - { type: "action", content: "...", camera_note: "中景" }
          - { type: "dialogue", speaker: "...", line: "...", emotion: "...", action: "...", camera_note: "特写" }
          - { type: "inner_voice", speaker: "...", line: "..." }
          - { type: "flashback", content: "..." }
          - { type: "screen_text", content: "..." }
          - { type: "sound_effect", content: "..." }
        conflict: { type, intensity: 1-5, description }
    ending_hook: { type, content, intensity: 1-5 }
emotion_curve: { phases: [...] }
quality_metrics: { avg_sentence_length, dialogue_ratio, ... }
```

`camera_note` 取值严格限制为 `特写 | 近景 | 中景 | 全景 | 远景`，不含运镜术语。

## 量化质量标准

| 指标 | 目标值 |
|------|--------|
| 句子长度 | 10-14 字符 |
| 对话比例 | 70-80% |
| 视觉标记密度 | 3-5 个/100 字 |
| 网文感关键词密度 | 1.5-2.5 个/100 字 |
| 情绪形容词密度 | ≤2 个/千字 |
| 动作描写占比 | ≥30% |
| 每集场景数 | 2-3 个 |
| 每集冲突数 | ≥2 个 |
| 3 秒入冲突 | 强制 |

## 项目文件结构（计划）

| 路径 | 用途 |
|------|------|
| `zmq/novel-to-script-team-分析文档.md` | 完整设计文档：筛选决策、YAML Schema、边界定义 |
| `novel-to-script-team/agents/` | 参考：10 个保留 Agent 的角色定义 |
| `novel-to-script-team/skills/` | 参考：12 个保留 Skill 的执行规则 |
| `novel-to-script-team/references/` | 参考：13 个保留 Reference 的方法论 |
| `novel-to-script-team/scripts/` | 参考：5 个保留 Script 工具 |
| `scripts/` | 本项目工具脚本（检索、生成等） |
| `outputs/{剧本名}/scripts/ep{N}.yaml` | 核心产物：YAML 格式结构化剧本 |

## Agent 工作流命令

```bash
~analyze          # 改编分析：文本清洗 + 洞察提炼
~plan             # 分集规划：分集目录 + 情绪曲线
~write N          # 写第 N 集（输出 YAML 格式剧本）
~review N         # 复核第 N 集
~final-check      # 工作流完成检查
~status           # 查询项目状态
```

## 状态管理

- 每个剧本独立状态文件：`outputs/{剧本名}/.agent-state.json`
- 同一集内复用 agentId 保持上下文连续
- 跨集自动清空 agentId 防止上下文溢出
- 项目记忆由 continuity-recorder 维护
- 所有 Agent 记录日志到 `outputs/{剧本名}/logs/{agent-name}.log`
