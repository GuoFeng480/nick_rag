"""Chroma 向量库封装。"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import chromadb
from langchain_community.vectorstores import Chroma

from app.api.embedding.base_embedding import BaseEmbedding
from app.api.vector_db.base_vector import BaseVector
from app.config.settings import Settings, get_settings


class ChromaVectorDB(BaseVector):
    """Chroma 向量库封装。

    支持本地或远程 Chroma 服务，提供写入与检索能力。
    """

    def __init__(
        self,
        embedding_function: BaseEmbedding,
        settings: Optional[Settings] = None,
        collection_name: Optional[str] = None,
        table_config: Optional[Any] = None,
    ) -> None:
        """初始化 Chroma 客户端与集合。

        参数:
            embedding_function: Embedding 接口实现。
            settings: 配置对象，包含 Chroma 连接信息。
            collection_name: 可选集合名，默认使用配置。
            table_config: 表配置（Chroma 忽略，仅用于统一接口）。
        """
        self.settings = settings or get_settings()
        _ = table_config
        if embedding_function is None:
            raise ValueError("embedding_function is required (use Hunyuan embeddings)")
        client = None
        if self.settings.chroma_host:
            headers = None
            if self.settings.chroma_api_key:
                headers = {self.settings.chroma_auth_header: self.settings.chroma_api_key}
            client = chromadb.HttpClient(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
                ssl=self.settings.chroma_ssl,
                headers=headers,
                tenant=self.settings.chroma_tenant or None,
                database=self.settings.chroma_database or None,
            )
        if not collection_name:
            raise ValueError("collection_name is required for ChromaVectorDB")
        self.store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_function,
            client=client,
        )

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """写入文本向量。

        参数:
            texts: 文本列表。
            metadatas: 元数据列表。
            ids: 自定义向量 ID。
        """
        return self.store.add_texts(list(texts), metadatas=metadatas, ids=ids)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """按相似度检索文本。

        参数:
            query: 查询文本。
            k: 返回数量。
            filter: 元数据过滤条件。
        """
        return self.store.similarity_search(query, k=k, filter=filter)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """按相似度检索文本并返回得分。

        说明:
            得分为 Chroma 返回的距离/相似度，具体含义由配置决定。
        """
        return self.store.similarity_search_with_score(query, k=k, filter=filter)



BaseVector.register_backend("chroma", ChromaVectorDB)
