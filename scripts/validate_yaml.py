#!/usr/bin/env python3
"""Validate an N2S YAML file when PyYAML is available.

The core CLI validates generated objects before writing them. This helper is
for users who later edit YAML files by hand and want a standalone check.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schema_validate import find_forbidden_terms, validate_script


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 N2S YAML 剧本")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)

    try:
        import yaml  # type: ignore
    except Exception:
        print("错误：独立解析 YAML 需要安装 PyYAML：python3 -m pip install PyYAML", file=sys.stderr)
        return 1

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = validate_script(data)
    errors.extend(find_forbidden_terms([path]))
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
