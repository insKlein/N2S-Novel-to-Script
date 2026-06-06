"""Schema checks for generated N2S YAML script objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List


CAMERA_NOTES = {"特写", "近景", "中景", "全景", "远景"}
ELEMENT_TYPES = {
    "action",
    "dialogue",
    "inner_voice",
    "flashback",
    "screen_text",
    "sound_effect",
}
FORBIDDEN_TERMS = {
    "Seedance",
    "Sora",
    "分镜",
    "镜号",
    "运镜",
    "推镜",
    "拉镜",
    "摇镜",
    "移镜",
    "转场",
    "视频提示词",
    "图片生成",
}


def validate_script(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in [
        "meta",
        "adaptation_summary",
        "naming_conventions",
        "episodes",
        "emotion_curve",
        "quality_metrics",
    ]:
        if key not in data:
            errors.append(f"缺少顶层字段: {key}")

    episodes = data.get("episodes", [])
    if not isinstance(episodes, list) or not episodes:
        errors.append("episodes 必须是非空数组")
        return errors

    for episode in episodes:
        number = episode.get("episode_number", "?")
        for key in ["episode_meta", "scenes", "ending_hook", "satisfaction_points"]:
            if key not in episode:
                errors.append(f"第 {number} 集缺少字段: {key}")
        scenes = episode.get("scenes", [])
        if not isinstance(scenes, list) or not scenes:
            errors.append(f"第 {number} 集 scenes 必须是非空数组")
            continue
        for scene in scenes:
            scene_id = scene.get("scene_id", "?")
            if "location" not in scene:
                errors.append(f"第 {number} 集第 {scene_id} 场缺少 location")
            if "conflict" not in scene:
                errors.append(f"第 {number} 集第 {scene_id} 场缺少 conflict")
            elements = scene.get("elements", [])
            if not isinstance(elements, list) or not elements:
                errors.append(f"第 {number} 集第 {scene_id} 场 elements 必须是非空数组")
                continue
            for idx, element in enumerate(elements, 1):
                element_type = element.get("type")
                if element_type not in ELEMENT_TYPES:
                    errors.append(
                        f"第 {number} 集第 {scene_id} 场元素 {idx} type 非法: {element_type}"
                    )
                camera_note = element.get("camera_note")
                if camera_note and camera_note not in CAMERA_NOTES:
                    errors.append(
                        f"第 {number} 集第 {scene_id} 场元素 {idx} camera_note 非法: {camera_note}"
                    )
    return errors


def find_forbidden_terms(paths: Iterable[Path]) -> List[str]:
    findings: List[str] = []
    for path in paths:
        if not path.exists() or path.is_dir():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for term in sorted(FORBIDDEN_TERMS):
            if term in text:
                findings.append(f"{path}: 包含越界词 {term}")
    return findings
