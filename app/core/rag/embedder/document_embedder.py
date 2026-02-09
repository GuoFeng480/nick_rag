"""文档入库组件。"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, Iterable, List, Optional

from app.core.rag.chunker import Chunker, UnstructuredChunker

from app.api.embedding.hunyuan import get_embeddings
from app.api.vector_db.base_vector import BaseVector
from app.config.settings import Settings, get_settings
from app.core.db.rag_documents import RagDocumentStore
from app.config.vector_schema import documents as documents_table
from unstructured.partition.auto import partition


class DocumentEmbedder:
    """文档入库与切分封装。

    负责解析文档、切分、写入向量库并记录元数据。
    """

    def __init__(
        self,
        vector_db: Optional[BaseVector] = None,
        metadata_store: Optional[RagDocumentStore] = None,
        chunker: Optional[Chunker] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        """初始化文档入库组件。

        参数:
            vector_db: 向量库写入实现。
            metadata_store: 文档元数据存储。
            settings: 配置对象。
        """
        self.settings = settings or get_settings()
        if vector_db is None:
            collection_name = documents_table.COLLECTION_NAME
            self.vector_db = BaseVector.from_settings(
                embedding_function=get_embeddings(self.settings),
                settings=self.settings,
                collection_name=collection_name,
                table_config=documents_table,
            )
        else:
            self.vector_db = vector_db
        self.metadata_store = metadata_store or RagDocumentStore(self.settings)
        self.chunker = chunker or UnstructuredChunker()

    def ingest_pdf(self, file_path: str, doc_info: Optional[Dict[str, Any]] = None) -> int:
        """解析并入库 PDF 文档。

        参数:
            file_path: PDF 文件路径。
            doc_info: 文档元数据字典。
        返回:
            文档 ID。
        """
        elements = self._load_file_elements(file_path)
        return self.ingest_elements(elements, source=file_path, doc_info=doc_info)

    def ingest_directory(
        self,
        dir_path: str,
        doc_info: Dict[str, Any],
        recursive: bool = True,
    ) -> List[int]:
        """从目录批量入库文档。

        说明:
            目录下 PDF/DOCX 文件均使用 Unstructured 解析后入库。
        参数:
            dir_path: 文档目录。
            doc_info: 统一的文档元数据（doc_type/year/version/status）。
            recursive: 是否递归子目录。
        返回:
            入库的文档 ID 列表。
        """
        if not doc_info:
            raise ValueError("doc_info is required for directory ingestion")
        doc_ids: List[int] = []
        for file_path in self._iter_files(dir_path, recursive=recursive):
            elements = self._load_file_elements(file_path)
            if not elements:
                continue
            per_file_info = dict(doc_info)
            per_file_info["filename"] = os.path.basename(file_path)
            doc_id = self.ingest_elements(elements, source=file_path, doc_info=per_file_info)
            doc_ids.append(doc_id)
        return doc_ids

    def ingest_elements(
        self,
        elements: List[Any],
        source: str,
        doc_info: Optional[Dict[str, Any]] = None,
    ) -> int:
        """将结构化元素切分后写入向量库。

        参数:
            elements: Unstructured 解析得到的元素列表。
            source: 文档来源标识。
            doc_info: 文档元数据字典。
        返回:
            文档 ID。
        """
        base_metadata = {"source": source}
        if doc_info:
            base_metadata.update(
                {
                    "doc_type": doc_info.get("doc_type"),
                    "year": doc_info.get("year"),
                    "version": doc_info.get("version"),
                    "status": doc_info.get("status"),
                    "filename": doc_info.get("filename"),
                    "effective_from": doc_info.get("effective_from"),
                    "effective_to": doc_info.get("effective_to"),
                }
            )
        chunks = self.chunker.chunk_elements(elements, base_metadata)
        doc_id = self._resolve_doc_id(source, doc_info)
        ids = []
        for idx, doc in enumerate(chunks):
            doc.metadata["doc_id"] = doc_id
            doc.metadata["chunk_id"] = idx
            ids.append(f"{doc_id}-{idx}")
        texts = [doc.page_content for doc in chunks]
        metadatas = [doc.metadata for doc in chunks]
        self.vector_db.add_texts(texts, metadatas=metadatas, ids=ids)
        if doc_info:
            self._upsert_document_info(doc_id, source, doc_info)
        return doc_id

    def _iter_files(self, dir_path: str, recursive: bool = True) -> Iterable[str]:
        """遍历目录内 PDF/DOCX 文件路径。"""
        allowed_exts = {".pdf", ".docx"}
        if recursive:
            for root, _, files in os.walk(dir_path):
                for name in files:
                    if os.path.splitext(name.lower())[1] not in allowed_exts:
                        continue
                    yield os.path.join(root, name)
        else:
            for name in os.listdir(dir_path):
                if os.path.splitext(name.lower())[1] not in allowed_exts:
                    continue
                file_path = os.path.join(dir_path, name)
                if os.path.isfile(file_path):
                    yield file_path

    def _load_file_elements(self, file_path: str) -> List[Any]:
        """使用 Unstructured 解析文件并返回元素列表。

        说明:
            由 Unstructured 负责切分策略，避免二次切分。
        """
        return list(
            partition(
                filename=file_path,
                chunking_strategy="by_title",
                max_characters=self.settings.chunk_size,
                new_after_n_chars=self.settings.chunk_size,
                combine_text_under_n_chars=max(200, int(self.settings.chunk_size * 0.5)),
                overlap=self.settings.chunk_overlap,
            )
        )

    def _resolve_doc_id(self, source: str, doc_info: Optional[Dict[str, Any]]) -> int:
        """确定文档 ID。

        优先使用 doc_info 中的 id，否则根据 source 生成稳定哈希。
        """
        if doc_info and doc_info.get("id") is not None:
            return int(doc_info["id"])
        return int(hashlib.sha1(source.encode("utf-8")).hexdigest()[:16], 16)

    def _upsert_document_info(self, doc_id: int, source: str, doc_info: Dict[str, Any]) -> None:
        """写入文档元数据记录。

        要求 doc_info 包含 doc_type/year/version/status。
        """
        required = ["doc_type", "year", "version", "status"]
        missing = [key for key in required if key not in doc_info]
        if missing:
            raise ValueError(f"Missing doc_info fields: {', '.join(missing)}")

        filename = doc_info.get("filename", source)
        vector_id = doc_info.get("vector_id")
        effective_from = doc_info.get("effective_from")
        effective_to = doc_info.get("effective_to")
        self.metadata_store.upsert_document(
            doc_id=doc_id,
            doc_type=doc_info["doc_type"],
            year=int(doc_info["year"]),
            version=int(doc_info["version"]),
            status=doc_info["status"],
            filename=filename,
            vector_id=vector_id,
            effective_from=effective_from,
            effective_to=effective_to,
        )

