# Novel-to-Script-Team 项目分析文档（筛选版）

> **项目地址**: https://github.com/Supreme-Ultimate/novel-to-script-team
> **目标项目**: AI 小说转剧本工具 — 将 3 章节以上小说自动转换为结构化剧本（YAML 格式）
> **筛选原则**: 保留剧本创作核心流水线（分析→分集→写集→审核），删除所有视频/分镜/图片生成相关内容

---

## 筛选总览

| 类别 | 原始数量 | 保留 | 删除 | 保留率 |
|------|---------|------|------|--------|
| Agent | 17 | 10 | 7 | 59% |
| Skill | 27 | 12 | 15 | 44% |
| Reference | 23 | 13 | 10 | 57% |
| Script | 10 | 5 | 5 | 50% |
| 流水线阶段 | 6 | 4+1 | 2 | — |

---

## 目录

1. [项目概述](#1-项目概述)
2. [核心设计决策：可拍性 vs 分镜的边界](#2-核心设计决策)
3. [核心流水线（筛选后保留4+1阶段）](#3-核心流水线)
4. [四层架构设计](#4-四层架构设计)
5. [Agent详解（保留10个 / 删除7个）](#5-agent详解)
6. [Skill技能系统（保留12个 / 删除15个）](#6-skill技能系统)
7. [Reference参考标准（保留13个 / 删除10个）](#7-reference参考标准)
8. [Script脚本工具（保留5个 / 删除5个）](#8-script脚本工具)
9. [状态管理机制（保留）](#9-状态管理机制)
10. [输出目录结构（精简版）](#10-输出目录结构)
11. [YAML Schema 设计方案](#11-yaml-schema-设计方案)

---

## 1. 项目概述

这是一个**基于多AI Agent协作的网文改编短剧全流程生产系统**。~~系统将中文网络小说自动转化为可直接用于拍摄的剧本、分镜板、美术设计和视频生成提示词。~~

> **筛选后定位**：将中文网络小说自动转化为结构化剧本（YAML格式），让作者获得可编辑、可进一步打磨的剧本初稿。

### 核心能力（筛选后）

- **输入**: ~~3章节以上的~~ 中文网络小说原文（或故事大纲/短剧素材）
- **输出**: 结构化剧本（YAML 格式）、改编分析报告、角色档案、分集规划、审核报告
- **特点**: 全程AI Agent驱动，每阶段有审核门控，支持断点续传

### 核心哲学

系统遵循 **"Generate → Review → Revise → Re-review → PASS"** 流程，每个关键阶段执行双重审核（业务审核 + 合规审核）。

---

## 2. 核心设计决策：可拍性 vs 分镜的边界

> 这是本次筛选最重要的设计决策。它决定了哪些内容属于"剧本创作"应保留，哪些属于"导演/分镜师工作"应删除。

### 2.1 三层边界模型

```
┌──────────────────────────────────────────────┐
│  第三层：导演分镜（删除）                       │
│  镜号序列、运镜方案（推拉摇移跟升降）、          │
│  九宫格节奏板、转场手法、Seedance提示词         │
│  → 属于导演/分镜师，不属于编剧                  │
├──────────────────────────────────────────────┤
│  第二层：编剧镜头意识（保留 — 轻量可选）         │
│  景别提示（特写/中景/全景）、关键动作强调        │
│  → 编剧用文字告诉读者"这一刻很重要，应放大"      │
│  → YAML中体现为 camera_note 可选字段            │
├──────────────────────────────────────────────┤
│  第一层：可拍性基本功（保留 — 强制）             │
│  用动作/表情/道具替代心理描写、Show Don't Tell   │
│  → 剧本区别于小说的本质特征                      │
│  → YAML 中体现为 action/dialogue 等结构化字段    │
└──────────────────────────────────────────────┘
```

### 2.2 每一层的具体示例

**第一层：可拍性基本功（强制，不可跳过）**

```
❌ 小说心理描写：
   林念感到无比绝望，她觉得整个世界都抛弃了她。

✅ 剧本可拍写法：
   △ 林念靠在冰封的墙边，嘴唇发紫，眼神空洞
   △ 手指无意识地抠着地面，指甲缝里渗出血丝
```

→ YAML 中对应 `type: "action"` 字段，是剧本的**强制组成部分**。

**第二层：镜头意识（可选，关键处标注）**

```yaml
# 关键情感爆发时刻 — 标注"建议特写"，强调面部表情
- type: "dialogue"
  speaker: "林念"
  line: "三年了，我对你掏心掏肺，你就是这么回报我的？"
  emotion: "压抑后爆发"
  camera_note: "特写"              # ← 可选字段

# 大场面 — 标注"全景"，帮助读者建立空间感
- type: "action"
  content: "萧家三百口人被押入刑场，跪倒一片"
  camera_note: "全景"

# 普通过渡对话 — 不标注
- type: "dialogue"
  speaker: "丫鬟"
  line: "小姐，该用膳了。"
  emotion: "平淡"
  # 没有 camera_note
```

→ YAML 中对应 **可选的** `camera_note` 字段，取值仅限于：`特写 | 近景 | 中景 | 全景 | 远景`，**不包含** 推拉摇移跟升降等运镜术语。

**第三层：导演分镜（完全删除）**

```
❌ 不属于剧本：镜号 + 景别 + 运镜 + 构图 + 时长
   镜号：S01-C03
   景别：中景→特写（推）
   运镜：缓慢推进，焦点从手镯移到眼神
   构图：对角线构图，女主在右下三分之一
   时长：4秒
```

→ 这些是分镜师/导演的工作产物，不是编剧的。删除。

### 2.3 边界判断标准

遇到一个内容不确定归属时，问一句：

> **"这个信息是写给演员/摄影看的，还是写给剪辑/后期看的？"**

- 写给**演员**的（动作、表情、语气、情绪）→ ✅ 剧本内容，保留
- 写给**摄影**的（基础景别建议、关键构图提示）→ ✅ 剧本可选（camera_note），保留
- 写给**剪辑**的（转场方式、时长控制、音画同步）→ ❌ 分镜/后期内容，删除
- 写给**特效师**的（粒子效果、CGI说明）→ ❌ 特效说明不是剧本，但 `【特效】` 标记可保留为轻量提示

### 2.4 对 Reference 筛选的影响

基于此边界模型，对 Reference 的筛选补充说明：

| Reference | 删除理由 | 是否有可提取部分 |
|-----------|----------|------------------|
| ~~08-camera-and-cinematography.md~~ | 90%内容为运镜/转场/进阶技法 | **景别基础（远全中近特）5种定义**可提取为 YAML Schema 的 camera_note 枚举值说明 |
| ~~09-storyboard-methodology.md~~ | 100%分镜内容 | 无 |
| ~~10a/10b/10c~~ | 面向视频拍摄的场景设计 | 无 |
| ~~19-micro-drama-storyboard-system.md~~ | 分镜两阶段系统 | 无 |
| ~~20-frame-description-elements.md~~ | 26元素帧描述框架 | 无 |

> 注：景别基础定义（远全中近特）不需要保留整个 reference 文件，只需要在 YAML Schema 文档中用 5 行说明即可。

---

## 3. 核心流水线（筛选后保留4+1阶段）

```
阶段0: 知识收编 (~ingest)                          ← ✅ 保留
  └─ knowledge-curator 扫描 sources/ → 去重 → 分级 → 更新知识库

阶段1: 改编分析 (~analyze)                          ← ✅ 保留
  └─ novel-analyzer → insight-architect → review-director
  └─ 产出: 清洗文本、分析报告、角色档案、洞察报告

阶段2: 分集规划 (~plan)                             ← ✅ 保留
  └─ episode-architect → emotion-architect → review-director
  └─ 产出: 分集目录、项目进度、情绪曲线

阶段3: 写集 (~write N)                              ← ✅ 保留（核心）
  └─ script-writer → visual-storyteller → review-director → continuity-recorder
  └─ 产出: 第N集剧本（YAML格式）、风格分析、视觉叙事报告、项目记忆更新

阶段4: 总复核 (~review N)                           ← ✅ 保留
  └─ script-comparator → review-director
  └─ 产出: 逐个对比分析、综合审核报告

阶段5A: 标准分镜流 (~storyboard-film N)             ← ❌ 删除（视频生成相关）
阶段5B: Seedance流 (~storyboard-seedance N)         ← ❌ 删除（视频生成相关）

阶段6: 最终检查 (~final-check)                      ← ✅ 保留
  └─ UTF-8乱码检查、称呼一致性检查、文件完整性检查
```

### ~~阶段5A：标准分镜流~~ ❌ 删除
> **删除理由**: 标准影视分镜（节拍拆解→九宫格分镜板→四宫格序列板→运镜提示词）属于视频制作前序工作，本项目聚焦"小说→剧本"，不需要分镜板。

### ~~阶段5B：Seedance流~~ ❌ 删除
> **删除理由**: Seedance 2.0 视频提示词生成（导演分析→美术设计→资产图→帧图→视频提示词）属于视频生成管线，与剧本创作工具无关。

---

## 4. 四层架构设计（保留）

系统采用严格分层的架构（四层全部保留）：

```
用户命令 (~analyze, ~write N 等)
  ↓
Agent 层 (10个专业角色，阶段负责人)     ← 原17个，删除7个视频相关Agent
  ↓
Skill 层 (12个执行步骤、检查清单)       ← 原27个，删除15个视频相关Skill
  ↓
Reference 层 (13个方法论、标准)          ← 原23个，删除10个视频相关Reference
  ↓
Script 层 (5个自动化工具脚本)            ← 原10个，删除5个视频/图片脚本
  ↓
Outputs/{剧本名}/ (阶段产物、审核记录、状态文件)
```

| 层 | 职责 | 回答的问题 |
|---|---|---|
| **Agent** | 决定"谁负责" | 谁来执行这个任务？ |
| **Skill** | 决定"怎么做" | 具体执行步骤是什么？ |
| **Reference** | 决定"判断标准" | 怎样算做好？边界在哪？ |
| **Script** | 处理"自动化工具" | 哪些操作可以脚本化？ |

---

## 5. Agent详解（保留10个 / 删除7个）

### 5.1 保留的 Agent（10个 — 剧本创作核心）

| Agent | 角色 | 技能 | 核心任务 | 保留理由 |
|-------|------|------|----------|----------|
| **novel-analyzer** | 小说分析师 | adaptation-analysis-skill | 文本清洗、性别频判定、冲突建模、角色档案 | 剧本创作第一步，必须保留 |
| **insight-architect** | 洞察架构师 | (直接读references/18) | "开天眼"方法论、揭示隐藏真相、设计核心冲突 | 改编分析核心，决定剧本深度 |
| **episode-architect** | 分集架构师 | episode-planning-skill | 分集目录、情绪曲线、卡点设计 | 多章节→多集转换的必要环节 |
| **emotion-architect** | 情绪设计师 | (直接读references/14) | 情绪曲线设计、心理预期管理、认知负荷控制 | 保证剧本情绪节奏合理 |
| **script-writer** | 编剧 | script-writing/hit-script-retrieval/style-analysis | 单集剧本创作、参考剧本检索、风格自分析 | **核心Agent**，YAML格式剧本的生成者 |
| **visual-storyteller** | 视觉叙事专家 | show-dont-tell-skill | 情绪→动作翻译、"Show Don't Tell"执行 | 保证剧本"可拍性"，非视频专属 |
| **review-director** | 审核导演 | script-review/compliance-review/comparative-review/style-analysis | 业务审核+合规审核双审、PASS/FAIL判定 | 质量门控核心 |
| **script-comparator** | 剧本对比师 | one-by-one-comparison-skill | 与Top5爆款剧本逐一对比（100分制） | 质量对标参考 |
| **continuity-recorder** | 连续性记录员 | continuity-record-skill | 跨集一致性跟踪、项目记忆维护 | 多章节/多集一致性保障 |
| **knowledge-curator** | 知识管理员 | knowledge-curation-skill | 知识入库、去重、分级、路由 | 知识库维护，可保留用于管理参考剧本库 |

### 5.2 删除的 Agent（7个 — 视频/分镜相关）

| Agent | 角色 | 删除理由 |
|-------|------|----------|
| ~~**storyboard-director**~~ | ~~分镜导演~~ | 负责分镜全流程协调和审核，纯视频制作环节 |
| ~~**storyboard-artist**~~ | ~~分镜师~~ | 节拍拆解→九宫格→四宫格→Seedance提示词，纯分镜工作 |
| ~~**storyboard-coach**~~ | ~~分镜教练~~ | 7周分镜练习计划，教学性质，与剧本生成无关 |
| ~~**art-designer**~~ | ~~美术设计师~~ | 角色/场景视觉设计提示词（用于AI生图），非剧本内容 |
| ~~**animator**~~ | ~~动画师~~ | 镜头运动/运镜提示词（用于AI视频），非剧本内容 |
| ~~**image-generator**~~ | ~~图片生成师~~ | 调用API生成角色图/场景图/帧图，纯图片生成 |
| ~~**image-to-prompt**~~ | ~~图片反推师~~ | 从图片反推提示词，图片分析工具，非剧本创作 |

---

## 6. Skill技能系统（保留12个 / 删除15个）

### 6.1 保留的 Skill（12个 — 剧本创作与审核）

| 技能 | 用途 | 关键量化标准 | 保留理由 |
|------|------|-------------|----------|
| **adaptation-analysis-skill** | 文本清洗、类型判定、冲突建模、角色一致性 | — | ~analyze 阶段核心 |
| **episode-planning-skill** | 分集目录、情绪曲线、卡点设计 | 每集7-10场景 | ~plan 阶段核心 |
| **script-writing-skill** | 核心写作，参考Top5爆款剧本 | 写作前强制"可控剧本三问" | **~write 阶段核心，需改造输出YAML** |
| **hit-script-retrieval-skill** | 混合检索（语义60%+关键词40%）参考剧本 | 从117部爆款短剧库检索 | 提升剧本质量的参考检索 |
| **style-analysis-skill** | 语言风格5维度分析 | 句长10-14字、对话比70-80%、视觉标记3-5/100字 | 剧本质量量化评估 |
| **one-by-one-comparison-skill** | 与5个参考剧本逐一深度对比（100分制） | 节奏20+对话25+视觉20+网文感20+结构15 | 最终复核深度对比 |
| **comparative-review-skill** | 跨6维度复合对比 | 节奏/对话/情绪/结构/重复/完整性 | 快速迭代对比 |
| **script-review-skill** | 业务审核：节奏、冲突、一致性、钩子强度 | 3秒入冲突，每30秒有进展，每集≥2冲突 | 质量门控必须 |
| **compliance-review-skill** | 合规红线：政治/暴力/色情/违法 | 零红线违规 | 安全审核必须 |
| **continuity-record-skill** | 连续性记录：剧情决策/角色变化/伏笔/爽点/风险 | — | 跨集一致性必须 |
| **show-dont-tell-skill** | 情绪形容词→可拍动作翻译 | 情绪形容词≤2/千字，动作描写≥30% | 剧本"可拍性"核心 |
| **knowledge-curation-skill** | 知识收编、5问过滤、A/B/C/D分级 | — | 知识库维护 |

### 6.2 删除的 Skill（15个 — 视频/分镜/图片相关）

| 技能 | 删除理由 |
|------|----------|
| ~~**storyboard-handoff-skill**~~ | 剧本到分镜的交接协调器，不需要分镜所以不需要交接 |
| ~~**director-skill**~~ | 剧本→导演讲戏本，面向视频拍摄，非剧本创作 |
| ~~**film-storyboard-skill**~~ | 传统影视分镜（节拍拆解→九宫格→四宫格），纯分镜工作 |
| ~~**seedance-storyboard-skill**~~ | Seedance 2.0视频提示词，视频生成工具链 |
| ~~**animator-skill**~~ | 运镜/动态提示词，AI视频生成 |
| ~~**art-design-skill**~~ | 服化道/角色场景视觉设计提示词，AI生图 |
| ~~**script-analysis-review-skill**~~ | 审核导演讲戏本，面向视频拍摄 |
| ~~**art-direction-review-skill**~~ | 审核服化道设计，AI生图相关 |
| ~~**storyboard-review-skill**~~ | 审核分镜板结构，纯分镜审核 |
| ~~**seedance-prompt-review-skill**~~ | 审核Seedance提示词，视频生成工具链 |
| ~~**storyboard-coaching-skill**~~ | 分镜教练教学，与剧本生成无关 |
| ~~**image-generation-skill**~~ | 调用API生图，AI图片生成 |
| ~~**image-to-prompt-skill**~~ | 图片反推提示词，图片分析 |
| ~~**seedance-storyboard-skill/templates/silent-version-template.md**~~ | 视频静音版本模板，视频制作 |

---

## 7. Reference参考标准（保留13个 / 删除10个）

### 7.1 保留的 Reference（13个 — 剧本创作方法）

| 文件 | 内容 | 保留理由 |
|------|------|----------|
| **00-first-principles.md** | 四大不可妥协约束 | 剧本创作的第一性原则（可拍性/留存性/一致性/可控性）仍然适用 |
| **01-adaptation-system.md** | 改编系统方法论 | 小说改编剧本的核心方法论 |
| **02-episode-architecture.md** | 分集架构方法论 | 多章节→多集拆分的指导标准 |
| **03-script-writing-standard.md** | 单集写作标准 | **核心参考**，包含格式标记系统、题材模板、钩子设计、金句公式等 |
| **04-review-gates.md** | 审核门控标准 | 剧本质量审核的方法论 |
| **05-compliance-boundaries.md** | 合规红线标准 | 内容安全审核边界 |
| **07-knowledge-curation.md** | 知识收编规则 | 参考剧本库管理 |
| **13-show-dont-tell-methodology.md** | Show Don't Tell方法论 | 剧本"可拍性"核心方法论，非视频专属 |
| **14-story-psychology.md** | 故事心理学 | 情绪曲线/爽感心理学，剧本质量关键 |
| **16-dramatic-principles.md** | 剧作原理 | 三幕结构/冲突设计/人物弧光，剧本创作基础 |
| **18-theme-selection-philosophy.md** | "开天眼"方法论 | 洞察提炼的核心哲学 |
| **21-agent-logging-standard.md** | Agent日志规范 | 系统运行规范 |
| **index.md** | 目录索引 | 文档导航 |
| **troubleshooting.md** | 故障排查 | 系统维护 |

### 7.2 删除的 Reference（10个 — 视频/分镜/视觉设计相关）

| 文件 | 删除理由 |
|------|----------|
| ~~**06-storyboard-handoff.md**~~ | 剧本→分镜桥接规范，不需要分镜 |
| ~~**08-camera-and-cinematography.md**~~ | 镜头/摄影/运镜方法论，视频拍摄用 |
| ~~**09-storyboard-methodology.md**~~ | 分镜板设计方法论，纯分镜内容 |
| ~~**10a-action-dialogue-scenes.md**~~ | 动作/对话场景设计（面向视频拍摄的场景设计技巧） |
| ~~**10b-atmosphere-fantasy.md**~~ | 氛围/奇幻视觉设计，面向AI视频生成 |
| ~~**10c-suspense-montage.md**~~ | 悬疑/蒙太奇设计，视频剪辑技法 |
| ~~**11a-seedance-prompt-methodology.md**~~ | Seedance 2.0提示词方法论，视频生成 |
| ~~**11b-image-motion-prompt.md**~~ | 图像/动态提示词，视频生成 |
| ~~**11c-sora2-rhythm-control.md**~~ | Sora2节奏控制，视频生成工具 |
| ~~**12-genre-specific-techniques.md**~~ | 类型化视觉技巧（玄幻/末世/女频的视觉化特效），面向视频 |
| ~~**15-color-psychology.md**~~ | 色彩心理学，视觉设计用 |
| ~~**17-lighting-narrative.md**~~ | 光影叙事，摄影/视频用 |
| ~~**19-micro-drama-storyboard-system.md**~~ | 微短剧分镜两阶段系统，纯分镜 |
| ~~**20-frame-description-elements.md**~~ | 帧图描述26元素框架，AI生图用 |

---

## 8. Script脚本工具（保留5个 / 删除5个）

### 8.1 保留的 Script（5个 — 检索与配置）

| 脚本 | 功能 | 保留理由 |
|------|------|----------|
| **env_config.py** | .env环境变量加载 | 基础配置工具 |
| **quick_search.py** | 轻量级关键词搜索 | 参考剧本检索（备选） |
| **improved_hybrid_search.py** | 混合检索引擎（语义60%+关键词40%） | 参考剧本检索（主力） |
| **test_retrieval.py** | 检索功能测试 | 检索系统验证 |
| **refresh_knowledge_registry.sh** | 知识注册表自动刷新 | 知识库维护 |

### 8.2 删除的 Script（5个 — 图片/视频生成）

| 脚本 | 删除理由 |
|------|----------|
| ~~**generate_image.py**~~ | 调用API批量生成角色图/场景图/帧图，纯图片生成 |
| ~~**reverse_prompt.py**~~ | 图片反推提示词，图片分析工具 |
| ~~**ava_skyreels_batch.py**~~ | SkyReels图生视频批处理，视频生成 |
| ~~**ave_still_batch.py**~~ | AVE静态图片批量生成，图片生成 |
| ~~**ave_composite_batch.py**~~ | AVE复合图片批量生成，图片生成 |

---

## 9. 状态管理机制（保留）

### 9.1 Resumable Subagents（断点续传）✅ 保留

**状态文件**: `outputs/{剧本名}/.agent-state.json`

```json
{
  "knowledge-curator": "",
  "novel-analyzer": "abc123",
  "episode-architect": "",
  "emotion-architect": "",
  "script-writer": "def456",
  "review-director": "",
  "script-comparator": "",
  "visual-storyteller": "",
  "continuity-recorder": "",
  "insight-architect": ""
}
```

> ~~原17个Agent的ID映射~~ → 精简为10个保留Agent的ID映射

**规则**:
- 同一集内复用agentId（保持上下文连续）
- 跨集清空所有agentId（防止上下文溢出）
- 每个剧本独立状态文件
- 恢复失败则降级为全新创建

### 9.2 项目记忆（Project Memory）✅ 保留

由`continuity-recorder`维护在`knowledge/project-memory.md`，跟踪：
- 剧情决策
- 角色状态变化
- 伏笔埋设与回收
- 集级爽点与反转
- 待处理一致性风险

### 9.3 日志标准 ✅ 保留

所有Agent按`references/21-agent-logging-standard.md`规范记录到`outputs/{剧本名}/logs/{agent-name}.log`

---

## 10. 输出目录结构（精简版）

```
outputs/{剧本名}/
├── .agent-state.json              # 断点续传状态（精简为10个Agent）
├── analysis/                      # 阶段1产出
│   ├── cleaned_text.txt           # 清洗后的小说原文
│   ├── 分析报告.md                # 改编分析报告
│   ├── 角色档案.md                # 角色档案
│   └── insight-report.md          # 洞察报告
├── planning/                      # 阶段2产出
│   ├── 分集目录.md                # 分集规划
│   └── 项目进度.md                # 项目进度
├── emotion-design/                # 情绪设计
│   ├── emotion-curve-ep<N>.md     # 单集情绪曲线
│   └── emotion-strategy.md        # 整体情绪策略
├── scripts/                       # 阶段3产出（核心）
│   └── ep{N}.yaml                 # ← 改为YAML格式的结构化剧本
├── review/                        # 阶段4产出
│   ├── review-log.md              # 审核日志
│   ├── style-analysis-ep<N>.md    # 风格分析
│   ├── visual-storytelling-report-ep<N>.md  # 视觉叙事报告
│   ├── comparative-review-ep<N>.md          # 快速对比审核
│   └── one-by-one-comparison-ep<N>.md       # 逐一深度对比
│
│   ~~storyboard/~~                ← ❌ 删除（分镜产物）
│   ~~assets/~~                    ← ❌ 删除（美术资产提示词）
│   ~~images/~~                    ← ❌ 删除（生成图片）
│
└── logs/                          # 日志
    ├── novel-analyzer.log
    ├── insight-architect.log
    ├── episode-architect.log
    ├── emotion-architect.log
    ├── script-writer.log
    ├── visual-storyteller.log
    ├── review-director.log
    ├── script-comparator.log
    ├── continuity-recorder.log
    └── knowledge-curator.log
```

---

## 11. YAML Schema 设计方案

> **说明**: 这是为"AI小说转剧本工具"新增的核心设计。原始项目使用 Markdown 格式输出剧本，我们需要改造为 YAML 格式以支持结构化编辑和程序化处理。

### 11.1 设计目标

1. **结构化可编辑**: 作者拿到 YAML 剧本后可以方便地修改任何字段
2. **完整信息承载**: 包含场景、对话、动作、情绪等所有剧本要素
3. **机器可解析**: 支持导入其他工具进行二次处理
4. **人类可读**: YAML 格式天然可读，无需特殊编辑器
5. **兼容 Markdown 渲染**: 可方便地转回 Markdown 用于展示

### 11.2 核心设计原则

| 原则 | 来源 | 说明 |
|------|------|------|
| **可拍性优先** | references/00 | 不可拍的信息（心理描写、抽象情绪）不进入剧本，转为动作/台词 |
| **一句一拳** | references/03 | 每句台词推进剧情、展现人物或制造冲突 |
| **格式标记保留** | references/03 | `※`场景标记、`△`动作标记、`【独白】`等标记转为结构化字段 |
| **可验证性** | references/04 | 每个字段都有明确的验证规则 |
| **镜头意识分层** | 见 §2 | 基础景别提示（camera_note）可选保留；运镜/转场/构图等技术细节不属于剧本 |

### 11.3 YAML Schema 完整定义

```yaml
# ============================================
# AI 小说转剧本工具 - 剧本 YAML Schema
# ============================================

# --- 元信息 ---
meta:
  script_title: "剧本标题"           # 剧本名称
  source_novel: "原著小说名"          # 来源小说
  author: "原作者"                   # 小说作者
  adapter: "AI"                     # 改编者
  version: "1.0"                    # 版本号
  created_at: "2026-06-06"          # 生成日期
  total_episodes: 80                # 总集数

# --- 改编分析摘要 ---
adaptation_summary:
  genre: "男频"                     # 性别频：男频/女频
  sub_genre: "重生复仇"              # 子类型
  target_audience: "25-40岁男性"     # 目标受众
  core_conflict: "主角前世被背叛，重生后复仇"  # 核心冲突
  main_characters:                  # 主要角色
    - name: "林念"
      role: "主角"
      archetype: "重生复仇者"
      traits: ["冷静", "果断", "隐忍"]
    - name: "陈俊"
      role: "反派"
      archetype: "负心人"
      traits: ["虚伪", "自私", "贪婪"]

# --- 称呼规范表 ---
naming_conventions:
  - character: "林念"
    aliases: ["念念", "林小姐", "林总"]
    forbidden: ["小念"]              # 禁止使用的称呼

# --- 分集列表 ---
episodes:
  - episode_number: 1
    title: "重生归来"
    # 单集元数据
    episode_meta:
      duration: "1-2分钟"            # 预估时长
      scene_count: 3                 # 场景数
      word_count: 650                # 字数
      emotion_peak: "愤怒→决心"       # 情绪走向
      hook_type: "重生悬念"           # 钩子类型

    # 场景列表
    scenes:
      - scene_id: 1
        # 场景标记（对应 ※）
        location:
          time: "深夜"
          place: "废弃工厂"
          environment: "暴风雪，零下80度"
          lighting: "昏暗"
        # 场景情绪
        emotion: "绝望→震惊"
        # 场景内元素
        elements:
          - type: "action"            # 动作描述（对应 △）
            content: "林念靠在冰封的墙边，嘴唇发紫，眼神空洞"
            camera_note: "中景"       # 可选：景别提示，仅限「特写/近景/中景/全景/远景」

          - type: "flashback"         # 闪回（对应 【闪回】）
            content: "前世片段快速闪过"
            camera_note: "特写"       # 可选：强调关键闪回画面

          - type: "dialogue"          # 对白
            speaker: "陈俊"
            line: "念念，我只爱你一个人。"
            emotion: "虚伪深情"
            action: "握住林念的手"     # 同步动作
            camera_note: "特写"       # 可选：关键情感台词建议特写

          - type: "inner_voice"       # 内心独白（对应 【独白】）
            speaker: "林念"
            line: "我...重生了？"
            max_length: 15            # 独白不超过15字

          - type: "screen_text"       # 屏幕文字（对应 【文字】）
            content: "距离末世降临：90天"

          - type: "sound_effect"      # 音效（对应 【音效】）
            content: "暴风雪呼啸声"

        # 场景冲突
        conflict:
          type: "内心冲突"             # 冲突类型
          intensity: 3                # 冲突强度 1-5
          description: "主角从绝望中发现自己重生"

    # 集尾钩子
    ending_hook:
      type: "悬念式"                  # 钩子类型
      content: "林念睁开眼，手机屏幕亮起——2025年6月15日"
      intensity: 4                    # 钩子强度 1-5

    # 爽点（如有）
    satisfaction_points:
      - position: "结尾"
        type: "重生觉醒"
        intensity: 3

# --- 整体情绪曲线 ---
emotion_curve:
  episodes: 80
  model: "波浪式上升"                  # 情绪模型
  phases:
    - name: "钩子期"
      episodes: "1-10"
      emotion_range: [2, 5]           # 情绪强度范围 1-5
      description: "快节奏强冲突，每集1个小冲突，3集1个小反转"
    - name: "爽点期"
      episodes: "11-40"
      emotion_range: [2, 5]
      description: "打压和爽感交替，主角逐步逆袭"
    - name: "升级期"
      episodes: "41-70"
      emotion_range: [3, 5]
      description: "核心冲突升级，幕后boss浮出水面"
    - name: "收官期"
      episodes: "71-80"
      emotion_range: [4, 5]
      description: "终极对决，圆满释放"

# --- 质量指标 ---
quality_metrics:
  avg_sentence_length: 12            # 平均句长（目标10-14字）
  dialogue_ratio: 0.75               # 对话比例（目标70-80%）
  visual_marker_density: 4.2         # 视觉标记密度（目标3-5/100字）
  web_novel_keyword_density: 2.0     # 网文感关键词密度（目标1.5-2.5/100字）
  emotion_adjective_density: 1.5     # 情绪形容词密度（目标≤2/千字）
  action_description_ratio: 0.35     # 动作描写占比（目标≥30%）
  review_status: "PASS"              # 审核状态
  review_score: 85                   # 综合评分
```

### 11.4 Schema 设计理由说明

| 设计决策 | 原因 |
|----------|------|
| **YAML而非JSON** | YAML更可读，支持注释，适合作者手动编辑；JSON适合程序间传输 |
| **YAML而非纯Markdown** | Markdown难以程序化解析每个元素；YAML可被任何语言解析，同时保持人类可读 |
| **episodes作为顶层数组** | 方便按集索引，每集独立可编辑；导入工具时可逐集处理 |
| **scenes 细分为 elements** | 原项目用 `※/△/【独白】` 等标记区分元素类型，Schema 将其结构化为 `location/action/dialogue/inner_voice` 等字段，既保留信息又便于解析 |
| **保留 camera_note 可选字段** | 虽然去掉了分镜系统，但基础景别提示帮助作者理解场景的视觉重点。取值严格限制为 `特写/近景/中景/全景/远景` 五种，不含运镜术语。只在关键情感/动作节点标注，普通过渡场景不标注。详见 §2 边界模型。 |
| **camera_note 为何不含运镜** | 推拉摇移跟升降属于导演/摄影指导的调度决策，涉及镜头运动速度、焦点转移、机械臂轨迹等技术参数，编剧不应越界。编剧只需标记"这个瞬间应该被强调"（通过特写），而不应规定"用推镜还是摇镜"。
| **emotion 字段贯穿多层级** | 从`adaptation_summary`到单集再到场景，逐级细化情绪设计；来源于emotion-architect |
| **conflict 强制字段** | 原项目要求每集≥2个冲突，Schema强制标注冲突类型和强度 |
| **ending_hook 必填** | 原项目强调每集结尾必须有强钩子，Schema强制此字段 |
| **quality_metrics 内置** | 将style-analysis-skill的量化指标直接嵌入Schema，让作者看到剧本质量评分 |
| **naming_conventions 独立字段** | 原项目通过continuity-recorder维护称呼一致性，Schema中独立存放便于全文校验 |
| **satisfaction_points 可选** | 不是每集都有爽点（打压集可能没有），设为可选 |

---

## 附录A: 筛选决策汇总表

### A.1 保留的Agent（10个）

| # | Agent | 阶段 |
|---|-------|------|
| 1 | knowledge-curator | 阶段0 |
| 2 | novel-analyzer | 阶段1 |
| 3 | insight-architect | 阶段1 |
| 4 | episode-architect | 阶段2 |
| 5 | emotion-architect | 阶段2 |
| 6 | script-writer | 阶段3 |
| 7 | visual-storyteller | 阶段3 |
| 8 | review-director | 阶段1-4 |
| 9 | script-comparator | 阶段4 |
| 10 | continuity-recorder | 阶段3+ |

### A.2 删除的Agent（7个）

| # | Agent | 删除理由 |
|---|-------|----------|
| 1 | storyboard-director | 分镜全流程协调，视频制作环节 |
| 2 | storyboard-artist | 分镜板生成，纯分镜内容 |
| 3 | storyboard-coach | 分镜教学，与剧本生成无关 |
| 4 | art-designer | 视觉设计提示词，AI生图用 |
| 5 | animator | 运镜提示词，AI视频用 |
| 6 | image-generator | API图片生成，非剧本内容 |
| 7 | image-to-prompt | 图片反推，非剧本内容 |

### A.3 保留的Skill（12个）

| # | Skill |
|---|-------|
| 1 | knowledge-curation-skill |
| 2 | adaptation-analysis-skill |
| 3 | episode-planning-skill |
| 4 | script-writing-skill |
| 5 | hit-script-retrieval-skill |
| 6 | style-analysis-skill |
| 7 | one-by-one-comparison-skill |
| 8 | comparative-review-skill |
| 9 | script-review-skill |
| 10 | compliance-review-skill |
| 11 | continuity-record-skill |
| 12 | show-dont-tell-skill |

### A.4 删除的Skill（15个）

| # | Skill | 删除理由 |
|---|-------|----------|
| 1 | storyboard-handoff-skill | 剧本→分镜桥接 |
| 2 | director-skill | 导演分析（面向拍摄） |
| 3 | film-storyboard-skill | 影视分镜板 |
| 4 | seedance-storyboard-skill | Seedance视频提示词 |
| 5 | animator-skill | 运镜提示词 |
| 6 | art-design-skill | 服化道视觉设计 |
| 7 | script-analysis-review-skill | 导演分析审核 |
| 8 | art-direction-review-skill | 美术设计审核 |
| 9 | storyboard-review-skill | 分镜结构审核 |
| 10 | seedance-prompt-review-skill | Seedance提示词审核 |
| 11 | storyboard-coaching-skill | 分镜教学 |
| 12 | image-generation-skill | API图片生成 |
| 13 | image-to-prompt-skill | 图片反推 |
| 14 | seedance-storyboard-skill/templates/* | 视频模板 |

### A.5 保留的Reference（13个）

| # | 文件 |
|---|------|
| 1 | 00-first-principles.md |
| 2 | 01-adaptation-system.md |
| 3 | 02-episode-architecture.md |
| 4 | 03-script-writing-standard.md |
| 5 | 04-review-gates.md |
| 6 | 05-compliance-boundaries.md |
| 7 | 07-knowledge-curation.md |
| 8 | 13-show-dont-tell-methodology.md |
| 9 | 14-story-psychology.md |
| 10 | 16-dramatic-principles.md |
| 11 | 18-theme-selection-philosophy.md |
| 12 | 21-agent-logging-standard.md |
| 13 | index.md / troubleshooting.md |

### A.6 删除的Reference（10个）

| # | 文件 | 删除理由 |
|---|------|----------|
| 1 | 06-storyboard-handoff.md | 分镜桥接 |
| 2 | 08-camera-and-cinematography.md | 镜头/摄影 |
| 3 | 09-storyboard-methodology.md | 分镜方法论 |
| 4 | 10a/10b/10c (3个) | 场景设计/氛围/蒙太奇 |
| 5 | 11a/11b/11c (3个) | Seedance/动态提示词/Sora2 |
| 6 | 12-genre-specific-techniques.md | 类型化视觉技巧 |
| 7 | 15-color-psychology.md | 色彩心理学 |
| 8 | 17-lighting-narrative.md | 光影叙事 |
| 9 | 19-micro-drama-storyboard-system.md | 分镜系统 |
| 10 | 20-frame-description-elements.md | 帧图元素 |

### A.7 保留的Script（5个）

| # | 脚本 |
|---|------|
| 1 | env_config.py |
| 2 | quick_search.py |
| 3 | improved_hybrid_search.py |
| 4 | test_retrieval.py |
| 5 | refresh_knowledge_registry.sh |

### A.8 删除的Script（5个）

| # | 脚本 | 删除理由 |
|---|------|----------|
| 1 | generate_image.py | API图片生成 |
| 2 | reverse_prompt.py | 图片反推 |
| 3 | ava_skyreels_batch.py | 视频批处理 |
| 4 | ave_still_batch.py | 图片批量 |
| 5 | ave_composite_batch.py | 图片合成 |

---

## 附录B: 命令集变更

### 保留的命令

| 命令 | 用途 |
|------|------|
| `~ingest` | 知识收编 |
| `~analyze` | 改编分析 |
| `~plan` | 分集规划 |
| `~write N` | 写第N集（输出YAML格式） |
| `~review N` | 复核第N集 |
| `~final-check` | 工作流完成检查 |
| `~status` | 查询项目状态 |
| `~help` | 帮助信息 |

### 删除的命令

| 命令 | 删除理由 |
|------|----------|
| ~~`~storyboard-film N`~~ | 标准分镜流 |
| ~~`~storyboard-seedance N`~~ | Seedance分镜流 |
| ~~`~generate-images N`~~ | 图片生成 |
| ~~`~reverse-prompt`~~ | 图片反推 |
| ~~`~storyboard-status`~~ | 分镜状态查询 |
| ~~`~ingest-pending`~~ | 可选删除（知识收编相关，如不需要可去） |

---

> **文档总结**: 原始项目是一个覆盖"小说→剧本→分镜→视频"的完整影视生产管线。筛选后我们保留"小说→剧本"的核心链路（10个Agent、12个Skill、13个Reference、5个Script），删除所有视频/分镜/图片生成相关组件（7个Agent、15个Skill、10个Reference、5个Script），并新增YAML Schema设计方向以满足"AI小说转剧本工具"的结构化输出需求。
