# Script Writing Standard

## 核心规则

- 一句一拳，每一句都要推进剧情、塑造人物或制造冲突。
- 台词短、直接、口语化。
- 每集必须有冲突和钩子。
- 抽象心理转为动作、道具、对白或简短独白。
- 输出必须符合 `docs/yaml-schema.md`。

## YAML 元素映射

- 场景信息 -> `location`
- 动作画面 -> `type: action`
- 对白 -> `type: dialogue`
- 内心独白 -> `type: inner_voice`
- 闪回 -> `type: flashback`
- 屏幕文字 -> `type: screen_text`
- 音效 -> `type: sound_effect`
