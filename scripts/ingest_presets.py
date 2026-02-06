"""命令行入口：同步预设问题向量。"""

from __future__ import annotations

import argparse

from app.core.rag.preset_embedder import PresetEmbedder


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="同步预设问题到向量库")
    parser.add_argument("--category", help="预设问题分类过滤", default=None)
    return parser


def main() -> None:
    """执行预设问题向量同步。"""
    parser = _build_parser()
    args = parser.parse_args()
    embedder = PresetEmbedder()
    count = embedder.sync_preset_questions(category=args.category)
    print(f"Synced preset questions: {count}")


if __name__ == "__main__":
    main()
