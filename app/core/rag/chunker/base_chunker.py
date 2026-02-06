"""切分器接口定义。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from langchain_core.documents import Document


class Chunker(ABC):
    """文档切分器抽象基类。"""

    @abstractmethod
    def chunk_elements(self, elements: List[Any], base_metadata: Dict[str, Any]) -> List[Document]:
        """将结构化元素切分为块。

        参数:
            elements: Unstructured 解析得到的元素列表。
            base_metadata: 应用于每个块的基础元数据。
        返回:
            切分后的文档列表。
        """
        raise NotImplementedError
