# N2S 剧本 YAML Schema

本文档定义 N2S 生成的结构化剧本格式。目标是让小说作者拿到一个可读、可编辑、可继续打磨的剧本初稿，同时让后续工具可以稳定解析。

## 顶层结构

```yaml
meta:
  script_title: "剧本标题"
  source_novel: "原著小说名"
  author: "原作者"
  adapter: "N2S AI"
  version: "0.1.0"
  created_at: "2026-06-06"
  total_episodes: 3

adaptation_summary:
  genre: "男频/女频/混合/待定"          # novel-analyzer 粗判
  sub_genre: "重生复仇"
  target_audience: "目标读者/观众"
  # --- genre-classifier 细粒度分类（新字段） ---
  genre_detail:
    primary_genre: "女频"
    sub_genre: "古代言情"
    sub_genre_detail: "经商种田"         # 精确到具体流派
    confidence: 85                      # 0-100，<70 必须询问用户
    alternative_genres:                 # 次选分类列表
      - genre: "女频"
        sub_genre: "古代言情"
        sub_genre_detail: "宫闱宅斗"
        confidence: 12
    user_queried: false                 # 是否触发了用户询问
    classification_basis: "主角从事商业活动，冲突以市场竞争为主"
    adaptation_notes:                   # 从 genre-taxonomy.md 匹配
      - "经商种田节奏友好——每集一个小商业里程碑"
      - "场景控制在店铺/府邸/集市即可，成本低"
      - "女主借势而非亲自出手——符合女频原则"
  # --- 以上为 genre-classifier 输出 ---
  core_conflict: "核心冲突"
  main_characters:
    - name: "角色名"
      role: "主角"
      archetype: "人物原型"
      traits: ["特征1", "特征2"]

naming_conventions:
  - character: "角色名"
    aliases: ["允许称呼"]
    forbidden: ["禁用称呼"]

episodes:
  - episode_number: 1
    title: "第1集标题"
    episode_meta:
      duration: "1-2分钟"
      scene_count: 3
      word_count: 650
      emotion_peak: "压抑→反击"
      hook_type: "证据悬念"
    scenes: []
    ending_hook:
      type: "悬念式"
      content: "集尾钩子内容"
      intensity: 5
    satisfaction_points: []

emotion_curve:
  episodes: 3
  model: "压力积累后释放"
  phases: []

quality_metrics:
  avg_sentence_length: 12
  dialogue_ratio: 0.75
  visual_marker_density: 4.0
  web_novel_keyword_density: 1.8
  emotion_adjective_density: 1.0
  action_description_ratio: 0.35
  review_status: "DRAFT"
  review_score: 80
```

## 场景结构

```yaml
scenes:
  - scene_id: 1
    location:
      time: "清晨"
      place: "主角住处"
      environment: "桌上散着旧照片"
      lighting: "自然光"
    emotion: "压抑→警觉"
    elements:
      - type: "action"
        content: "主角盯着手机屏幕，指尖停在未接来电上。"
        camera_note: "特写"
      - type: "dialogue"
        speaker: "主角"
        line: "这一次，我不会再退。"
        emotion: "克制"
        action: "把旧照片扣在桌面"
      - type: "inner_voice"
        speaker: "主角"
        line: "该你还债了。"
      - type: "flashback"
        content: "三年前的录音画面闪过。"
      - type: "screen_text"
        content: "录音时间：三年前"
      - type: "sound_effect"
        content: "录音播放键轻响。"
    conflict:
      type: "关系压迫"
      intensity: 4
      description: "对手逼迫主角让步，主角拿出反证。"
```

## 字段约束

- `episodes`：必须是非空数组；每个 YAML 文件通常只保存当前集，也可以保存多集合集。
- `scenes`：每集必须有场景，MVP 推荐 2-3 场。
- `elements[].type`：只能是 `action`、`dialogue`、`inner_voice`、`flashback`、`screen_text`、`sound_effect`。
- `camera_note`：可选，只能是 `特写`、`近景`、`中景`、`全景`、`远景`。
- `conflict.intensity` 和 `ending_hook.intensity`：使用 1-5 分，5 为最强。
- `naming_conventions`：用于防止跨集称呼漂移。

## 设计原因

- 选择 YAML：比纯 Markdown 更容易被程序解析，比 JSON 更适合作者手动阅读和编辑。
- 保留 `meta`：记录剧名、来源、版本和集数，方便后续迭代。
- 独立 `adaptation_summary`：把小说分析结果放进剧本文件，作者不需要来回翻分析报告。
- 独立 `naming_conventions`：长篇改编最容易出现称呼、人设和关系漂移，此字段便于自动检查。
- 使用 `episodes -> scenes -> elements`：对应剧本创作的自然层级，也能承接原参考项目的场景标记、动作、对白、独白、字幕和音效。
- 强制 `conflict` 和 `ending_hook`：短剧初稿不能只是复述情节，每集都需要冲突推进和结尾钩子。
- 保留轻量 `camera_note`：编剧可以标出关键时刻的视觉重点，但只允许基础景别，不进入导演制作决策。
- 内置 `quality_metrics`：把句长、对白比例、动作描写比例等量化指标直接给作者，便于后续打磨。
