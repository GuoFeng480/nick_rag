"""命令行入口：初始化 Tencent VectorDB 数据库与集合。"""

from __future__ import annotations

import argparse

from app.api.embedding.hunyuan import get_embeddings
from app.api.vector_db.tencent_client import TencentVectorDB
from app.config.settings import get_settings
from app.config.vector_schema import documents as documents_table
from app.config.vector_schema import preset_questions as preset_table


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="初始化 Tencent VectorDB")
    parser.add_argument(
        "--table",
        choices=["documents", "preset_questions", "all"],
        default="documents",
        help="选择要初始化的集合",
    )
    parser.add_argument("--collection", help="集合名（可选，默认使用配置）")
    parser.add_argument("--dimension", type=int, help="向量维度（可选）")
    return parser


def _ensure_schema(table_config, collection_name: str | None, dimension: int | None) -> None:
    settings = get_settings()
    vector_db = TencentVectorDB(
        embedding_function=get_embeddings(settings),
        settings=settings,
        collection_name=collection_name,
        table_config=table_config,
    )
    vector_db.ensure_schema(dimension=dimension)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if args.table == "all":
        _ensure_schema(documents_table, None, args.dimension)
        _ensure_schema(preset_table, None, args.dimension)
    else:
        table = documents_table if args.table == "documents" else preset_table
        _ensure_schema(table, args.collection, args.dimension)
    print("Tencent VectorDB schema ensured.")


if __name__ == "__main__":
    main()
