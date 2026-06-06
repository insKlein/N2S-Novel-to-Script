"""FastAPI wrapper for the N2S CLI workflow."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from n2s import (  # noqa: E402
    command_analyze,
    command_convert,
    command_final_check,
    command_plan,
    command_review,
    command_write,
    project_dir,
    read_text,
)


app = FastAPI(title="N2S API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConvertRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    novel_text: str = Field(min_length=1, max_length=120_000)
    episodes: int = Field(default=3, ge=1, le=20)
    keywords: str = ""
    mock: bool = False


class StageRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    novel_text: str | None = Field(default=None, max_length=120_000)
    episodes: int = Field(default=3, ge=1, le=20)
    keywords: str = ""
    mock: bool = False


def _runtime_error(exc: RuntimeError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _temp_input(text: str) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False)
    with handle:
        handle.write(text)
    return Path(handle.name)


def _read_optional(path: Path) -> str:
    return read_text(path) if path.exists() else ""


def _episode_number(path: Path) -> int:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return int(digits or "0")


def _project_payload(title: str) -> dict[str, Any]:
    root = project_dir(title)
    if not root.exists():
        raise HTTPException(status_code=404, detail="项目不存在")

    scripts = sorted((root / "scripts").glob("ep*.yaml"))
    reports = {
        "analysis": _read_optional(root / "analysis" / "分析报告.md"),
        "characters": _read_optional(root / "analysis" / "角色档案.md"),
        "insight": _read_optional(root / "analysis" / "insight-report.md"),
        "planning": _read_optional(root / "planning" / "分集目录.md"),
        "emotion": _read_optional(root / "emotion-design" / "emotion-strategy.md"),
        "final_check": _read_optional(root / "final-check-report.md"),
    }
    return {
        "title": title,
        "project_dir": str(root),
        "episodes": [
            {"episode": _episode_number(path), "path": str(path), "yaml": read_text(path)}
            for path in scripts
        ],
        "reports": reports,
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/convert")
def convert(request: ConvertRequest) -> dict[str, Any]:
    temp_path = _temp_input(request.novel_text)
    try:
        command_convert(
            argparse.Namespace(
                input=str(temp_path),
                title=request.title,
                episodes=request.episodes,
                keywords=request.keywords,
                mock=request.mock,
            )
        )
        return _project_payload(request.title)
    except RuntimeError as exc:
        raise _runtime_error(exc) from exc
    finally:
        temp_path.unlink(missing_ok=True)


@app.post("/api/analyze")
def analyze(request: StageRequest) -> dict[str, Any]:
    if not request.novel_text:
        raise HTTPException(status_code=400, detail="analyze 需要 novel_text")
    temp_path = _temp_input(request.novel_text)
    try:
        command_analyze(
            argparse.Namespace(input=str(temp_path), title=request.title, mock=request.mock)
        )
        return _project_payload(request.title)
    except RuntimeError as exc:
        raise _runtime_error(exc) from exc
    finally:
        temp_path.unlink(missing_ok=True)


@app.post("/api/plan")
def plan(request: StageRequest) -> dict[str, Any]:
    try:
        command_plan(
            argparse.Namespace(title=request.title, episodes=request.episodes, mock=request.mock)
        )
        return _project_payload(request.title)
    except RuntimeError as exc:
        raise _runtime_error(exc) from exc


@app.post("/api/write/{episode}")
def write_episode(episode: int, request: StageRequest) -> dict[str, Any]:
    try:
        command_write(
            argparse.Namespace(
                title=request.title,
                episode=episode,
                keywords=request.keywords,
                mock=request.mock,
            )
        )
        return _project_payload(request.title)
    except RuntimeError as exc:
        raise _runtime_error(exc) from exc


@app.post("/api/review/{episode}")
def review_episode(episode: int, request: StageRequest) -> dict[str, Any]:
    try:
        command_review(argparse.Namespace(title=request.title, episode=episode))
        command_final_check(argparse.Namespace(title=request.title))
        return _project_payload(request.title)
    except RuntimeError as exc:
        raise _runtime_error(exc) from exc


@app.get("/api/projects/{title}")
def get_project(title: str) -> dict[str, Any]:
    return _project_payload(title)


@app.get("/api/projects/{title}/episodes/{episode}")
def get_episode(title: str, episode: int) -> dict[str, Any]:
    root = project_dir(title)
    path = root / "scripts" / f"ep{episode}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail="剧集不存在")
    return {"title": title, "episode": episode, "path": str(path), "yaml": read_text(path)}
