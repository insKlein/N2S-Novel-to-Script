#!/usr/bin/env python3
"""Search local authorized hit-script references by keywords."""

from __future__ import annotations

import argparse
from pathlib import Path


def quick_search(query: str, n_results: int = 5) -> list[dict[str, str]]:
    md_dir = Path("knowledge/hit-scripts-md")
    if not md_dir.exists():
        return []

    words = [word for word in query.split() if word]
    results = []
    for md_file in md_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        score = sum(1 for word in words if word in content)
        if score:
            results.append(
                {
                    "filename": md_file.name,
                    "filepath": str(md_file),
                    "score": str(score),
                    "preview": content[:300],
                }
            )
    results.sort(key=lambda item: int(item["score"]), reverse=True)
    return results[:n_results]


def main() -> None:
    parser = argparse.ArgumentParser(description="检索本地授权参考剧本")
    parser.add_argument("query")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    results = quick_search(args.query, args.top)
    if not results:
        print("未找到参考剧本。可将有权使用的 .md 文件放入 knowledge/hit-scripts-md/")
        return
    for index, result in enumerate(results, 1):
        print(f"{index}. {result['filename']} score={result['score']}")
        print(f"   {result['filepath']}")
        print(f"   {result['preview'][:120]}...")


if __name__ == "__main__":
    main()
