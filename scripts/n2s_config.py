"""Configuration helpers for N2S.

The project intentionally uses only the Python standard library so the CLI can
run in a fresh environment. Values in the real process environment override
values loaded from `.env`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parent.parent


def load_env() -> Dict[str, str]:
    values: Dict[str, str] = {}
    env_path = ROOT / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")

    for key, value in os.environ.items():
        if value:
            values[key] = value
    return values


def required(values: Dict[str, str], name: str) -> str:
    value = values.get(name, "").strip()
    if not value:
        raise RuntimeError(f"请在 .env 或环境变量中配置 {name}")
    return value


def optional(values: Dict[str, str], name: str, default: str = "") -> str:
    return values.get(name, "").strip() or default


def chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"
