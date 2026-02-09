"""基于 Unstructured 元素的切分器。

该切分器假定 Unstructured 已完成切分，
仅负责将元素转换为 Document 并补充元数据。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from langchain_core.documents import Document

from app.core.rag.chunker.base_chunker import Chunker


class UnstructuredChunker(Chunker):
    """Unstructured 元素切分器。"""

    def chunk_elements(self, elements: List[Any], base_metadata: Dict[str, Any]) -> List[Document]:
        """将 Unstructured 元素转换为 Document。

        说明:
            该实现不再二次切分，直接使用 Unstructured 的切分结果。
        """
        documents: List[Document] = []
        for element in elements:
            text = getattr(element, "text", None)
            if not text:
                continue
            meta = dict(base_metadata)
            meta.update(self._extract_metadata(element))
            documents.append(Document(page_content=text, metadata=meta))
        return documents

    def _extract_metadata(self, element: Any) -> Dict[str, Any]:
        meta: Dict[str, Any] = {}
        unstructured_meta: Dict[str, Any] = {
            "element_type": getattr(element, "category", None),
            "element_id": getattr(element, "id", None),
        }
        raw_meta = getattr(element, "metadata", None)
        if raw_meta is not None:
            if hasattr(raw_meta, "to_dict"):
                raw_dict = raw_meta.to_dict()
            else:
                raw_dict = {
                    key: value
                    for key, value in vars(raw_meta).items()
                    if not key.startswith("_")
                }
            for key, value in raw_dict.items():
                if value is None:
                    continue
                unstructured_meta[key] = value
        unstructured_meta = {key: value for key, value in unstructured_meta.items() if value is not None}
        if unstructured_meta:
            meta["unstructured_metadata"] = json.dumps(unstructured_meta, ensure_ascii=True)
            meta["unstructured_element_type"] = unstructured_meta.get("element_type")
            meta["unstructured_page_number"] = unstructured_meta.get("page_number")
        return {key: value for key, value in meta.items() if value is not None}
