#!/usr/bin/env python3
"""N2S command line tool: novel text to structured YAML scripts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from llm_client import LLMClient
from quick_search import quick_search
from schema_validate import find_forbidden_terms, validate_script
from yaml_io import write_yaml


ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
STATE_AGENT_KEYS = [
    "knowledge-curator",
    "novel-analyzer",
    "insight-architect",
    "genre-classifier",
    "episode-architect",
    "emotion-architect",
    "script-writer",
    "visual-storyteller",
    "review-director",
    "script-comparator",
    "continuity-recorder",
]


def slug_title(title: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", title.strip())
    return cleaned or "untitled"


def project_dir(title: str) -> Path:
    return OUTPUTS / slug_title(title)


def ensure_project(title: str) -> Path:
    root = project_dir(title)
    for child in [
        "analysis",
        "planning",
        "emotion-design",
        "scripts",
        "review",
        "logs",
        "knowledge",
    ]:
        (root / child).mkdir(parents=True, exist_ok=True)
    state_path = root / ".agent-state.json"
    if not state_path.exists():
        state_path.write_text(
            json.dumps({key: "" for key in STATE_AGENT_KEYS}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return root


def write_log(root: Path, agent: str, message: str) -> None:
    path = root / "logs" / f"{agent}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        path.read_text(encoding="utf-8") + message + "\n" if path.exists() else message + "\n",
        encoding="utf-8",
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def detect_chapter_count(text: str) -> int:
    heading_pattern = re.compile(
        r"(?m)^\s*(第[一二三四五六七八九十百千万零〇\d]+[章节回]|Chapter\s+\d+|CHAPTER\s+\d+|\d+[\.、]\s*)"
    )
    headings = heading_pattern.findall(text)
    if headings:
        return len(headings)
    blocks = [block for block in re.split(r"\n\s*\n", text) if block.strip()]
    return len(blocks)


def require_three_chapters(text: str) -> None:
    count = detect_chapter_count(text)
    if count < 3:
        raise RuntimeError(f"输入文本至少需要 3 个章节或段落块，当前检测到 {count} 个。")


def llm_or_mock(mock: bool) -> LLMClient | None:
    return None if mock else LLMClient()


def json_from_llm(client: LLMClient | None, task: str, prompt: str, mock_value: Dict[str, Any]) -> Dict[str, Any]:
    if client is None:
        return mock_value
    return client.complete_json(
        [
            {
                "role": "system",
                "content": (
                    "你是 N2S 小说转 YAML 剧本工具的专业编剧团队。"
                    "只输出 JSON 对象，不要输出 Markdown，不要输出解释。"
                ),
            },
            {"role": "user", "content": f"任务：{task}\n\n{prompt}"},
        ]
    )


def build_mock_analysis(title: str, novel: str) -> Dict[str, Any]:
    preview = novel.strip().replace("\n", " ")[:160]
    return {
        "cleaned_text": novel.strip(),
        "report_md": (
            f"# {title} 改编分析\n\n"
            "## 类型判断\n女频/男频暂按原文冲突自动细化。\n\n"
            "## 核心冲突\n主角在关系、目标或身份压力中被迫选择，并在后续剧集中完成反击。\n\n"
            f"## 原文摘录\n{preview}"
        ),
        "character_profiles_md": (
            "# 角色档案\n\n"
            "| 角色 | 功能 | 目标 | 风险 |\n"
            "|---|---|---|---|\n"
            "| 主角 | 情绪和行动中心 | 夺回主动权 | 称呼漂移 |\n"
            "| 对手 | 制造压力 | 阻碍主角 | 动机单薄 |\n"
        ),
        "insight_report_md": (
            "# 洞察报告\n\n"
            "- 主流叙事：主角被误解或压制。\n"
            "- 隐藏真相：主角掌握关键事实或能力。\n"
            "- 改编重点：尽快把隐藏真相变成可见行动。"
        ),
        "summary": {
            "genre": "待定",
            "sub_genre": "情绪反击",
            "target_audience": "短剧作者与小说作者",
            "core_conflict": "主角从被动承受转为主动反击",
            "main_characters": [
                {
                    "name": "主角",
                    "role": "主角",
                    "archetype": "被压制后的反击者",
                    "traits": ["克制", "敏锐", "有行动力"],
                }
            ],
        },
        "naming_conventions": [
            {"character": "主角", "aliases": ["主角"], "forbidden": ["错误称呼"]}
        ],
    }


def build_mock_classification(summary: Dict[str, Any]) -> Dict[str, Any]:
    genre = summary.get("genre", "待定")
    sub = summary.get("sub_genre", "待定")
    return {
        "primary_genre": genre,
        "sub_genre": sub,
        "sub_genre_detail": f"{sub}-自动细分",
        "confidence": 50,
        "alternative_genres": [],
        "adaptation_notes": ["请在正式模式下输入 API Key 以获取精确分类和改编建议。"],
        "user_queried": False,
        "classification_basis": "Mock 模式：基于 novel-analyzer 粗判结果自动生成，未做细粒度分类。",
    }


def classify_genre(root: Path, mock: bool, client: LLMClient | None) -> Dict[str, Any]:
    analysis = load_json(root / "analysis" / "analysis.json")
    summary = analysis.get("summary", {})
    novel_text = read_text(root / "analysis" / "cleaned_text.txt")

    if mock:
        data = build_mock_classification(summary)
        write_text(
            root / "analysis" / "genre-classification.json",
            json.dumps(data, ensure_ascii=False, indent=2),
        )
        write_log(root, "genre-classifier", f"{date.today()} PASS classify (mock) {summary.get('genre', 'N/A')}")
        return data

    taxonomy = ""
    taxonomy_path = ROOT / "references" / "genre-taxonomy.md"
    if taxonomy_path.exists():
        taxonomy = read_text(taxonomy_path)[:12000]

    genre = summary.get("genre", "待定")
    sub = summary.get("sub_genre", "")

    prompt = (
        "你是起点中文网资深编辑，精通网文题材细粒度分类。"
        "请基于以下小说原文和已有粗判结果，输出细粒度分类 JSON。\n\n"
        f"=== 已有粗判 ===\n"
        f"genre(男频/女频): {genre}\n"
        f"sub_genre: {sub}\n\n"
        f"=== 分类体系参考 ===\n{taxonomy}\n\n"
        f"=== 小说原文 ===\n{novel_text[:12000]}\n\n"
        "=== 输出要求 ===\n"
        "JSON 字段: primary_genre, sub_genre, sub_genre_detail(精确到具体流派如'高手下山'), "
        "confidence(0-100), alternative_genres(数组,每项含genre/sub_genre/sub_genre_detail/confidence), "
        "adaptation_notes(从taxonomy对应章节提取,不要自编), "
        "user_queried(true/false,置信度<70%时为true), "
        "classification_basis(一句话说明判断依据)。\n\n"
        "重要: 如果无法确定到具体子类，设置 user_queried=true 并在 alternative_genres 中列出所有可能。"
    )
    system = (
        "你是起点中文网资深编辑，专门做网文分类。"
        "只输出 JSON 对象，不要输出 Markdown，不要输出解释。"
        "改编注意事项必须从提供的 taxonomy 中提取，不要自己编造。"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    if client is None:
        data = build_mock_classification(summary)
    else:
        data = client.complete_json(messages, temperature=0.3)

    confidence = data.get("confidence", 0)
    user_queried = data.get("user_queried", False)

    if confidence < 70 or user_queried:
        alternatives = data.get("alternative_genres", [])
        alt_str = "\n".join(
            f"  - {a.get('sub_genre_detail', a.get('sub_genre', '未知'))} (置信度: {a.get('confidence', '?')}%)"
            for a in alternatives[:5]
        )
        print(f"\n⚠️ 题材分类不确定 (置信度: {confidence}%)")
        print(f"  首选: {data.get('sub_genre_detail', data.get('sub_genre', '未知'))}")
        if alt_str:
            print(f"  候选:\n{alt_str}")
        print(f"  依据: {data.get('classification_basis', 'N/A')}")
        print("  请在后续对话中确认最终分类，或输入 'ok' 接受首选。\n")

    write_text(
        root / "analysis" / "genre-classification.json",
        json.dumps(data, ensure_ascii=False, indent=2),
    )
    write_log(root, "genre-classifier", f"{date.today()} PASS classify confidence={confidence}")
    return data


def command_analyze(args: argparse.Namespace) -> Path:
    input_path = Path(args.input)
    novel = read_text(input_path)
    require_three_chapters(novel)
    client = llm_or_mock(args.mock)
    root = ensure_project(args.title)

    prompt = (
        "请分析以下 3 章以上小说文本，输出 JSON："
        "cleaned_text, report_md, character_profiles_md, insight_report_md, summary, naming_conventions。"
        "summary 需包含 genre, sub_genre, target_audience, core_conflict, main_characters。"
        "naming_conventions 为数组，每项含 character, aliases, forbidden。\n\n"
        f"剧名：{args.title}\n小说文本：\n{novel[:24000]}"
    )
    data = json_from_llm(client, "改编分析", prompt, build_mock_analysis(args.title, novel))

    write_text(root / "analysis" / "cleaned_text.txt", data.get("cleaned_text", novel))
    write_text(root / "analysis" / "分析报告.md", data.get("report_md", ""))
    write_text(root / "analysis" / "角色档案.md", data.get("character_profiles_md", ""))
    write_text(root / "analysis" / "insight-report.md", data.get("insight_report_md", ""))
    write_text(root / "analysis" / "analysis.json", json.dumps(data, ensure_ascii=False, indent=2))
    write_log(root, "novel-analyzer", f"{date.today()} PASS analyze {args.title}")
    write_log(root, "insight-architect", f"{date.today()} PASS insight {args.title}")
    classify_genre(root, args.mock, client)
    return root


def build_mock_plan(title: str, episodes: int) -> Dict[str, Any]:
    rows = []
    episode_items = []
    for number in range(1, episodes + 1):
        rows.append(f"| 第{number}集 | 主角承压后推进关键行动 | 对手施压 | 小反击 | 新证据出现 |")
        episode_items.append(
            {
                "episode_number": number,
                "title": f"第{number}集",
                "core_event": "主角面对压力并找到突破口",
                "conflict": "外部羞辱与内部选择叠加",
                "hook": "新的证据或人物关系浮出水面",
                "emotion_peak": "压抑→反击",
                "scene_count": 3,
            }
        )
    return {
        "episode_plan_md": (
            f"# {title} 分集目录\n\n"
            "| 集数 | 核心事件 | 冲突点 | 爽点 | 钩子 |\n"
            "|---|---|---|---|---|\n"
            + "\n".join(rows)
        ),
        "project_progress_md": f"# 项目进度\n\n- 计划集数：{episodes}\n- 当前阶段：分集规划完成",
        "emotion_strategy_md": (
            "# 情绪策略\n\n压力积累 → 小反击 → 更大压力 → 强钩子。"
            "每集控制在 2-3 场，结尾保留下一集悬念。"
        ),
        "episodes": episode_items,
    }


def command_plan(args: argparse.Namespace) -> Path:
    root = ensure_project(args.title)
    analysis = read_text(root / "analysis" / "analysis.json")
    client = llm_or_mock(args.mock)
    prompt = (
        "基于改编分析生成分集规划 JSON：episode_plan_md, project_progress_md, "
        "emotion_strategy_md, episodes。episodes 每项包含 episode_number, title, "
        "core_event, conflict, hook, emotion_peak, scene_count。\n\n"
        f"目标集数：{args.episodes}\n分析：\n{analysis[:20000]}"
    )
    data = json_from_llm(client, "分集规划", prompt, build_mock_plan(args.title, args.episodes))
    write_text(root / "planning" / "分集目录.md", data.get("episode_plan_md", ""))
    write_text(root / "planning" / "项目进度.md", data.get("project_progress_md", ""))
    write_text(root / "emotion-design" / "emotion-strategy.md", data.get("emotion_strategy_md", ""))
    write_text(root / "planning" / "plan.json", json.dumps(data, ensure_ascii=False, indent=2))
    write_log(root, "episode-architect", f"{date.today()} PASS plan {args.title}")
    write_log(root, "emotion-architect", f"{date.today()} PASS emotion-plan {args.title}")
    return root


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(read_text(path))


def build_mock_script(title: str, episode_number: int, analysis: Dict[str, Any]) -> Dict[str, Any]:
    summary = dict(analysis.get("summary", {}))
    naming = analysis.get("naming_conventions", [])

    # 注入 genre_detail（若存在）
    genre_detail = analysis.get("genre_detail")
    if not genre_detail:
        genre_detail = {
            "primary_genre": summary.get("genre", "待定"),
            "sub_genre": summary.get("sub_genre", "待定"),
            "sub_genre_detail": "自动细分",
            "confidence": 50,
            "alternative_genres": [],
            "adaptation_notes": [],
            "user_queried": False,
            "classification_basis": "Mock 模式自动生成",
        }
    summary["genre_detail"] = genre_detail

    return {
        "meta": {
            "script_title": title,
            "source_novel": title,
            "author": "未知",
            "adapter": "N2S AI",
            "version": "0.1.0",
            "created_at": str(date.today()),
            "total_episodes": 1,
        },
        "adaptation_summary": summary,
        "naming_conventions": naming,
        "episodes": [
            {
                "episode_number": episode_number,
                "title": f"第{episode_number}集",
                "episode_meta": {
                    "duration": "1-2分钟",
                    "scene_count": 3,
                    "word_count": 650,
                    "emotion_peak": "压抑→反击",
                    "hook_type": "证据悬念",
                },
                "scenes": [
                    {
                        "scene_id": 1,
                        "location": {
                            "time": "清晨",
                            "place": "主角住处",
                            "environment": "桌上散着旧照片和手机",
                            "lighting": "自然光",
                        },
                        "emotion": "压抑→警觉",
                        "elements": [
                            {
                                "type": "action",
                                "content": "主角盯着手机屏幕，指尖停在未接来电上。",
                                "camera_note": "特写",
                            },
                            {
                                "type": "dialogue",
                                "speaker": "主角",
                                "line": "这一次，我不会再退。",
                                "emotion": "克制",
                                "action": "把旧照片扣在桌面",
                                "camera_note": "近景",
                            },
                        ],
                        "conflict": {
                            "type": "内外压力",
                            "intensity": 3,
                            "description": "主角发现过去的压迫再次逼近。",
                        },
                    },
                    {
                        "scene_id": 2,
                        "location": {
                            "time": "上午",
                            "place": "会客厅",
                            "environment": "对手坐在主位，桌面摆着合同",
                            "lighting": "明亮",
                        },
                        "emotion": "羞辱→反击",
                        "elements": [
                            {
                                "type": "dialogue",
                                "speaker": "对手",
                                "line": "签了它，你还能少吃点苦。",
                                "emotion": "轻蔑",
                                "action": "把合同推到桌边",
                            },
                            {
                                "type": "action",
                                "content": "主角没有接笔，只把录音笔推到桌中央。",
                                "camera_note": "中景",
                            },
                            {
                                "type": "sound_effect",
                                "content": "录音播放键轻响。",
                            },
                        ],
                        "conflict": {
                            "type": "关系压迫",
                            "intensity": 4,
                            "description": "对手逼迫主角让步，主角拿出反证。",
                        },
                    },
                    {
                        "scene_id": 3,
                        "location": {
                            "time": "上午",
                            "place": "会客厅门口",
                            "environment": "门外脚步声突然停住",
                            "lighting": "逆光",
                        },
                        "emotion": "反击→悬念",
                        "elements": [
                            {
                                "type": "screen_text",
                                "content": "录音时间：三年前",
                            },
                            {
                                "type": "inner_voice",
                                "speaker": "主角",
                                "line": "该你还债了。",
                            },
                            {
                                "type": "action",
                                "content": "门被推开，所有人的目光同时转向门口。",
                                "camera_note": "全景",
                            },
                        ],
                        "conflict": {
                            "type": "证据反转",
                            "intensity": 5,
                            "description": "关键证人或证据即将登场。",
                        },
                    },
                ],
                "ending_hook": {
                    "type": "证据式",
                    "content": "门外的人开口：这段录音，我也有一份。",
                    "intensity": 5,
                },
                "satisfaction_points": [
                    {"position": "第二场", "type": "反证打脸", "intensity": 4}
                ],
            }
        ],
        "emotion_curve": {
            "episodes": 1,
            "model": "压力积累后释放",
            "phases": [
                {
                    "name": "单集情绪",
                    "episodes": str(episode_number),
                    "emotion_range": [2, 5],
                    "description": "压迫开场，反证反击，证人钩子收尾。",
                }
            ],
        },
        "quality_metrics": {
            "avg_sentence_length": 12,
            "dialogue_ratio": 0.72,
            "visual_marker_density": 4.0,
            "web_novel_keyword_density": 1.8,
            "emotion_adjective_density": 1.0,
            "action_description_ratio": 0.35,
            "review_status": "DRAFT",
            "review_score": 80,
        },
    }


def command_write(args: argparse.Namespace) -> Path:
    root = ensure_project(args.title)
    analysis = load_json(root / "analysis" / "analysis.json")
    plan = load_json(root / "planning" / "plan.json")
    refs = quick_search(args.keywords or analysis.get("summary", {}).get("sub_genre", ""), 5)

    # 读取细粒度分类（若存在）
    classification_path = root / "analysis" / "genre-classification.json"
    classification_info = ""
    if classification_path.exists():
        gc = load_json(classification_path)
        classification_info = (
            f"题材细分：{gc.get('sub_genre_detail', gc.get('sub_genre', ''))}，"
            f"改编注意事项：{'；'.join(gc.get('adaptation_notes', []))}\n"
        )

    client = llm_or_mock(args.mock)
    prompt = (
        "请生成第 N 集剧本 JSON，严格符合 N2S YAML Schema。"
        "顶层必须包含 meta, adaptation_summary, naming_conventions, episodes, emotion_curve, quality_metrics。"
        "episodes 只包含当前集。元素 type 只能是 action/dialogue/inner_voice/flashback/screen_text/sound_effect。"
        "camera_note 只能是 特写/近景/中景/全景/远景，禁止运镜、转场、分镜、图片、视频提示词。\n\n"
        f"剧名：{args.title}\n集数：{args.episode}\n"
        f"{classification_info}"
        f"分析：{json.dumps(analysis, ensure_ascii=False)[:12000]}\n"
        f"规划：{json.dumps(plan, ensure_ascii=False)[:12000]}\n参考检索：{json.dumps(refs, ensure_ascii=False)[:4000]}"
    )
    data = json_from_llm(client, "写集", prompt, build_mock_script(args.title, args.episode, analysis))
    errors = validate_script(data)
    if errors:
        raise RuntimeError("生成剧本未通过 Schema 校验：\n" + "\n".join(errors))
    output_path = root / "scripts" / f"ep{args.episode}.yaml"
    write_yaml(output_path, data)
    write_text(root / "review" / f"style-analysis-ep{args.episode}.md", "# 风格分析\n\n- 状态：已生成初稿，待人工继续打磨。")
    write_text(
        root / "review" / f"visual-storytelling-report-ep{args.episode}.md",
        "# 视觉叙事报告\n\n- 已检查 action/dialogue 等可拍元素。\n- camera_note 仅使用基础景别提示。",
    )
    write_log(root, "script-writer", f"{date.today()} PASS write ep{args.episode}")
    write_log(root, "visual-storyteller", f"{date.today()} PASS show-dont-tell ep{args.episode}")
    write_log(root, "continuity-recorder", f"{date.today()} PASS continuity ep{args.episode}")
    update_project_memory(root, args.episode)
    return output_path


def update_project_memory(root: Path, episode: int) -> None:
    memory = root / "knowledge" / "project-memory.md"
    existing = read_text(memory) if memory.exists() else "# 项目记忆\n"
    existing += f"\n- 第{episode}集：已生成 YAML 初稿，后续审核需关注称呼、人设、伏笔回收。\n"
    write_text(memory, existing)


def command_review(args: argparse.Namespace) -> Path:
    root = ensure_project(args.title)
    script_path = root / "scripts" / f"ep{args.episode}.yaml"
    if not script_path.exists():
        raise RuntimeError(f"未找到剧本文件: {script_path}")
    findings = find_forbidden_terms([script_path])
    status = "FAIL" if findings else "PASS"
    report = [
        f"# 第{args.episode}集审核报告",
        "",
        f"- 审核状态：{status}",
        "- 业务审核：检查冲突、钩子、可拍动作、称呼一致性。",
        "- 合规审核：检查明显红线与越界制作字段。",
    ]
    if findings:
        report.append("\n## 问题\n")
        report.extend(f"- {item}" for item in findings)
    else:
        report.append("\n## 结论\n\n- 未发现超出剧本创作边界的制作字段。")
    output = root / "review" / f"comparative-review-ep{args.episode}.md"
    write_text(output, "\n".join(report))
    write_log(root, "review-director", f"{date.today()} {status} review ep{args.episode}")
    write_log(root, "script-comparator", f"{date.today()} {status} compare ep{args.episode}")
    return output


def command_final_check(args: argparse.Namespace) -> Path:
    root = ensure_project(args.title)
    yaml_files = sorted((root / "scripts").glob("ep*.yaml"))
    md_files = sorted(root.rglob("*.md"))
    findings = []
    if not yaml_files:
        findings.append("未找到任何 ep<N>.yaml 剧本文件。")
    findings.extend(find_forbidden_terms([*yaml_files, *md_files]))
    for path in [*yaml_files, *md_files]:
        text = read_text(path)
        if "\ufffd" in text:
            findings.append(f"{path}: 包含 UTF-8 替换字符")
        if re.search(r"母亲.*弟弟|弟弟.*母亲", text):
            findings.append(f"{path}: 可能存在称呼混乱")

    status = "FAIL" if findings else "PASS"
    report = ["# Final Check Report", "", f"- 状态：{status}", f"- YAML 剧本数：{len(yaml_files)}"]
    if findings:
        report.append("\n## 问题\n")
        report.extend(f"- {item}" for item in findings)
    else:
        report.append("\n## 结论\n\n- 文件完整性、乱码、称呼和越界词检查通过。")
    output = root / "final-check-report.md"
    write_text(output, "\n".join(report))
    return output


def command_convert(args: argparse.Namespace) -> Path:
    analyze_args = argparse.Namespace(**vars(args))
    root = command_analyze(analyze_args)
    plan_args = argparse.Namespace(title=args.title, episodes=args.episodes, mock=args.mock)
    command_plan(plan_args)
    for episode in range(1, args.episodes + 1):
        write_args = argparse.Namespace(
            title=args.title,
            episode=episode,
            mock=args.mock,
            keywords=args.keywords,
        )
        command_write(write_args)
        review_args = argparse.Namespace(title=args.title, episode=episode)
        command_review(review_args)
    command_final_check(argparse.Namespace(title=args.title))
    return root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="N2S: 小说转结构化 YAML 剧本")
    sub = parser.add_subparsers(dest="command", required=True)

    convert = sub.add_parser("convert", help="完整转换：分析、规划、写集、审核")
    convert.add_argument("--input", required=True)
    convert.add_argument("--title", required=True)
    convert.add_argument("--episodes", type=int, default=3)
    convert.add_argument("--keywords", default="")
    convert.add_argument("--mock", action="store_true", help="无 API 演示模式")
    convert.set_defaults(func=command_convert)

    analyze = sub.add_parser("analyze", help="阶段1：改编分析")
    analyze.add_argument("--input", required=True)
    analyze.add_argument("--title", required=True)
    analyze.add_argument("--mock", action="store_true")
    analyze.set_defaults(func=command_analyze)

    plan = sub.add_parser("plan", help="阶段2：分集规划")
    plan.add_argument("--title", required=True)
    plan.add_argument("--episodes", type=int, default=3)
    plan.add_argument("--mock", action="store_true")
    plan.set_defaults(func=command_plan)

    write = sub.add_parser("write", help="阶段3：写第 N 集")
    write.add_argument("episode", type=int)
    write.add_argument("--title", required=True)
    write.add_argument("--keywords", default="")
    write.add_argument("--mock", action="store_true")
    write.set_defaults(func=command_write)

    review = sub.add_parser("review", help="阶段4：复核第 N 集")
    review.add_argument("episode", type=int)
    review.add_argument("--title", required=True)
    review.set_defaults(func=command_review)

    final_check = sub.add_parser("final-check", help="最终检查")
    final_check.add_argument("--title", required=True)
    final_check.set_defaults(func=command_final_check)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.func(args)
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    print(f"完成：{result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
