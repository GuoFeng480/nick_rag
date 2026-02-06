"""命令行入口：批量入库文档目录。"""

from __future__ import annotations

import argparse

from app.core.rag.embedder.document_embedder import DocumentEmbedder


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="批量入库文档目录")
    parser.add_argument("dir_path", help="文档目录路径")
    parser.add_argument("--doc-type", required=False, help="文档类型")
    parser.add_argument("--year", required=False, type=int, help="文档年份")
    parser.add_argument("--version", required=False, type=int, help="文档版本")
    parser.add_argument("--status", default="active", help="文档状态")
    parser.add_argument("--effective-from", help="生效起始日期，如 2024-01-01")
    parser.add_argument("--effective-to", help="生效结束日期，如 2024-12-31")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="交互式输入元数据",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="不递归子目录",
    )
    return parser


def main() -> None:
    """执行文档目录入库。"""
    parser = _build_parser()
    args = parser.parse_args()
    if args.interactive:
        if not args.doc_type:
            args.doc_type = input("文档类型: ").strip()
        if args.year is None:
            year_text = input("文档年份: ").strip()
            args.year = int(year_text) if year_text else None
        if args.version is None:
            version_text = input("文档版本: ").strip()
            args.version = int(version_text) if version_text else None
        if not args.status:
            args.status = "active"
        if args.effective_from is None:
            args.effective_from = input("生效起始日期(可选): ").strip() or None
        if args.effective_to is None:
            args.effective_to = input("生效结束日期(可选): ").strip() or None

    missing = []
    if not args.doc_type:
        missing.append("--doc-type")
    if args.year is None:
        missing.append("--year")
    if args.version is None:
        missing.append("--version")
    if missing:
        raise SystemExit(f"Missing required args: {', '.join(missing)}")
    embedder = DocumentEmbedder()
    doc_info = {
        "doc_type": args.doc_type,
        "year": args.year,
        "version": args.version,
        "status": args.status,
        "effective_from": args.effective_from,
        "effective_to": args.effective_to,
    }
    doc_ids = embedder.ingest_directory(
        args.dir_path,
        doc_info=doc_info,
        recursive=not args.no_recursive,
    )
    print(f"Ingested documents: {len(doc_ids)}")


if __name__ == "__main__":
    main()
