"""Small YAML writer for the N2S generated structure.

It writes readable YAML without requiring PyYAML. The validator can optionally
use PyYAML if the user installs it, but the CLI itself has no hard dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def dumps_yaml(value: Any, indent: int = 0) -> str:
    lines = _dump(value, indent)
    return "\n".join(lines) + "\n"


def write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_yaml(value), encoding="utf-8")


def _dump(value: Any, indent: int) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, str) and "\n" in item:
                lines.append(f"{pad}{key}: |")
                for raw_line in item.splitlines() or [""]:
                    lines.append(f"{pad}  {raw_line}")
            elif isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(_dump(item, indent + 2))
            else:
                lines.append(f"{pad}{key}: {_scalar(item)}")
        return lines

    if isinstance(value, list):
        if not value:
            return [f"{pad}[]"]
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{pad}-")
                lines.extend(_dump(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{pad}-")
                lines.extend(_dump(item, indent + 2))
            else:
                lines.append(f"{pad}- {_scalar(item)}")
        return lines

    return [f"{pad}{_scalar(value)}"]
