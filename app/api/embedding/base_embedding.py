"""Embedding 接口定义。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """Embedding 抽象基类。

    约定实现类需提供文本向量化接口，返回值为二维/一维浮点向量。
    """

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化。

        参数:
            texts: 待向量化的文本列表。
        返回:
            向量列表，与输入文本一一对应。
        """
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """单条查询向量化。

        参数:
            text: 查询文本。
        返回:
            单条向量表示。
        """
        raise NotImplementedError
