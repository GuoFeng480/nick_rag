"""Tencent VectorDB 客户端封装。

该模块封装腾讯向量数据库的写入与检索操作，
核心职责：
1) 负责鉴权与客户端初始化；
2) 将文本转换为向量并写入；
3) 将检索结果还原为 Document 结构。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from langchain_core.documents import Document
from tcvectordb import RPCVectorDBClient
from tcvectordb.model.document import SearchParams
from tcvectordb.model.enum import FieldType, IndexType, MetricType, ReadConsistency
from tcvectordb.model.index import FilterIndex, HNSWParams, Index, VectorIndex

from app.api.embedding.base_embedding import BaseEmbedding
from app.api.vector_db.base_vector import BaseVector
from app.config.settings import Settings, get_settings
from app.config.vector_schema import documents as default_table


class TencentVectorDB(BaseVector):
    """Tencent Cloud VectorDB 封装。

    说明:
        使用 tcvectordb 官方 SDK 的 VectorDBClient。
        该实现遵循 BaseVector 接口，提供写入与检索能力。
    """

    def __init__(
        self,
        embedding_function: BaseEmbedding,
        settings: Optional[Settings] = None,
        collection_name: Optional[str] = None,
        table_config: Optional[Any] = None,
    ) -> None:
        """初始化向量数据库客户端。

        参数:
            embedding_function: Embedding 接口实现。
            settings: 配置对象，包含向量数据库连接信息。
            collection_name: 可选集合名，默认使用配置。
        """
        self.settings = settings or get_settings()
        if embedding_function is None:
            raise ValueError("embedding_function is required")
        self.embedding_function = embedding_function

        if not self.settings.tencent_vdb_url:
            raise ValueError("Tencent VectorDB url is required")
        if not self.settings.tencent_vdb_database:
            raise ValueError("Tencent VectorDB database is required")

        if not self.settings.tencent_vdb_key:
            raise ValueError("Tencent VectorDB key is required")

        self.client = RPCVectorDBClient(
            url=self.settings.tencent_vdb_url,
            username=self.settings.tencent_vdb_username,
            key=self.settings.tencent_vdb_key,
            password=self.settings.tencent_vdb_password or None,
            read_consistency=self._parse_read_consistency(self.settings.tencent_vdb_read_consistency),
            timeout=self.settings.tencent_vdb_timeout,
            pool_size=self.settings.tencent_vdb_pool_size,
        )
        self.table_config = table_config or default_table
        # collection_name 可用于覆写默认集合，常用于预设问题等场景。
        self.collection_name = collection_name or self.table_config.COLLECTION_NAME
        if not self.collection_name:
            raise ValueError("Tencent VectorDB collection is required")
        self.database_name = self.settings.tencent_vdb_database
        self.text_field = self.table_config.TEXT_FIELD
        self.metadata_field = self.table_config.METADATA_FIELD
        self.vector_field = self.table_config.VECTOR_FIELD
        self.id_field = self.table_config.ID_FIELD
        self.filter_fields = list(self.table_config.FILTER_FIELDS)
        self.numeric_fields = {name for name in self.table_config.NUMERIC_FIELDS}

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

        说明:
            - 文本先通过 embedding_function 转为向量；
            - 构造向量列表后调用 Upsert 动作写入。
        """
        text_list = list(texts)
        if not text_list:
            return []
        # 批量向量化，确保与文本一一对应。
        vectors = self.embedding_function.embed_documents(text_list)
        # 元数据缺省时补空字典，避免长度不一致。
        metadata_list = metadatas or [{} for _ in text_list]
        # 若未指定 ID，使用序号字符串生成。
        id_list = ids or [str(i) for i in range(len(text_list))]
        payload_vectors = []
        for idx, text in enumerate(text_list):
            metadata = dict(metadata_list[idx]) if idx < len(metadata_list) else {}
            metadata = {key: value for key, value in metadata.items() if value is not None}
            for field in self.numeric_fields:
                if field in metadata:
                    metadata[field] = self._coerce_numeric(metadata[field])
            payload = {
                self.id_field: id_list[idx],
                self.vector_field: vectors[idx],
                self.text_field: text,
                self.metadata_field: metadata,
            }
            for field in self.filter_fields:
                if field in metadata and metadata[field] is not None:
                    payload[field] = metadata[field]
            payload_vectors.append(
                payload
            )
        self.client.upsert(
            database_name=self.database_name,
            collection_name=self.collection_name,
            documents=payload_vectors,
        )
        return id_list

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """按相似度检索文本。

        说明:
            返回 Document 列表，不包含 score。
        """
        results, _ = self._search(query, k=k, filter=filter)
        return results

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Document, Optional[float]]]:
        """按相似度检索文本并返回得分。

        说明:
            得分字段的语义由向量库 API 决定，可能是相似度或距离。
        """
        docs, scores = self._search(query, k=k, filter=filter)
        return list(zip(docs, scores))

    def _search(
        self,
        query: str,
        k: int,
        filter: Optional[Dict[str, Any]],
    ) -> Tuple[List[Document], List[Optional[float]]]:
        # 先对查询进行向量化。
        vector = self.embedding_function.embed_query(query)
        filter_expr = self._normalize_filter(filter)
        params = None
        if self.table_config.HNSW_EF_SEARCH > 0:
            params = SearchParams(ef=self.table_config.HNSW_EF_SEARCH)
        resp = self.client.search(
            database_name=self.database_name,
            collection_name=self.collection_name,
            vectors=[vector],
            filter=filter_expr,
            params=params,
            limit=k,
            output_fields=[
                self.text_field,
                self.metadata_field,
                self.id_field,
                *self.filter_fields,
            ],
        )
        documents, scores = self._extract_results(resp)
        return documents, scores

    def _parse_read_consistency(self, value: str) -> ReadConsistency:
        raw = (value or "").strip().lower()
        if raw in {"strong", "strong_consistency", "strongconsistency"}:
            return ReadConsistency.STRONG_CONSISTENCY
        return ReadConsistency.EVENTUAL_CONSISTENCY

    def ensure_database(self) -> None:
        """确保数据库存在。"""
        self.client.create_database_if_not_exists(database_name=self.database_name)

    def ensure_collection(self, dimension: Optional[int] = None) -> None:
        """确保集合存在，并按配置创建索引。"""
        vector_dim = dimension or self._resolve_dimension()
        index = self._build_index(vector_dim)
        self.client.create_collection_if_not_exists(
            database_name=self.database_name,
            collection_name=self.collection_name,
            shard=self.table_config.SHARD,
            replicas=self.table_config.REPLICAS,
            description=self.table_config.DESCRIPTION or None,
            index=index,
        )

    def ensure_schema(self, dimension: Optional[int] = None) -> None:
        """确保数据库与集合均存在。"""
        self.ensure_database()
        self.ensure_collection(dimension=dimension)

    def _resolve_dimension(self) -> int:
        if self.table_config.DIMENSION > 0:
            return self.table_config.DIMENSION
        sample = "dimension_probe"
        vector = self.embedding_function.embed_query(sample)
        return len(vector)

    def _build_index(self, dimension: int) -> Index:
        index = Index()
        index.add(
            FilterIndex(
                name=self.id_field,
                field_type=FieldType.String,
                index_type=IndexType.PRIMARY_KEY,
            )
        )
        vector_index = self._build_vector_index(dimension)
        index.add(vector_index)
        for field in self.filter_fields:
            if field == self.id_field:
                continue
            field_type = FieldType.Uint64 if field in self.numeric_fields else FieldType.String
            index.add(FilterIndex(name=field, field_type=field_type, index_type=IndexType.FILTER))
        return index

    def _build_vector_index(self, dimension: int) -> VectorIndex:
        index_type = self._parse_index_type(self.table_config.INDEX_TYPE)
        metric_type = self._parse_metric_type(self.table_config.METRIC_TYPE)
        params = HNSWParams(
            m=self.table_config.HNSW_M,
            efconstruction=self.table_config.HNSW_EF_CONSTRUCTION,
        )
        return VectorIndex(
            name=self.vector_field,
            field_type=FieldType.Vector,
            index_type=index_type,
            dimension=dimension,
            metric_type=metric_type,
            params=params,
        )


BaseVector.register_backend("tencent", TencentVectorDB)

    def _parse_index_type(self, value: str) -> IndexType:
        raw = (value or "").strip().upper()
        if raw == "HNSW":
            return IndexType.HNSW
        if raw == "IVF_FLAT":
            return IndexType.IVF_FLAT
        if raw == "IVF_PQ":
            return IndexType.IVF_PQ
        if raw == "IVF_SQ8":
            return IndexType.IVF_SQ8
        if raw == "IVF_SQ16":
            return IndexType.IVF_SQ16
        return IndexType.FLAT

    def _parse_metric_type(self, value: str) -> MetricType:
        raw = (value or "").strip().upper()
        if raw == "IP":
            return MetricType.IP
        if raw == "L2":
            return MetricType.L2
        return MetricType.COSINE

    def _normalize_filter(self, filter: Optional[Union[Dict[str, Any], str]]) -> Optional[str]:
        if filter is None:
            return None
        if isinstance(filter, dict) and "filter" in filter and len(filter) == 1:
            filter = filter["filter"]
        if isinstance(filter, dict):
            return self._dict_filter_to_expr(filter)
        if isinstance(filter, str):
            return filter
        return None

    def _dict_filter_to_expr(self, filter_dict: Dict[str, Any]) -> Optional[str]:
        parts: List[str] = []
        for key, value in filter_dict.items():
            if isinstance(value, dict):
                if "$in" in value:
                    parts.append(self._in_expr(key, value["$in"]))
                    continue
                if "in" in value:
                    parts.append(self._in_expr(key, value["in"]))
                    continue
                if "$eq" in value:
                    parts.append(self._eq_expr(key, value["$eq"]))
                    continue
                if "eq" in value:
                    parts.append(self._eq_expr(key, value["eq"]))
                    continue
                continue
            if isinstance(value, list):
                parts.append(self._in_expr(key, value))
                continue
            parts.append(self._eq_expr(key, value))
        if not parts:
            return None
        return " and ".join(parts)

    def _eq_expr(self, key: str, value: Any) -> str:
        return f"{key} = {self._format_value(self._normalize_value(key, value))}"

    def _in_expr(self, key: str, values: Iterable[Any]) -> str:
        formatted = ",".join(
            self._format_value(self._normalize_value(key, value))
            for value in values
        )
        return f"{key} in ({formatted})"

    def _normalize_value(self, key: str, value: Any) -> Any:
        if key in self.numeric_fields:
            return self._coerce_numeric(value)
        return value

    def _coerce_numeric(self, value: Any) -> Any:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            text = value.strip()
            if text.isdigit():
                return int(text)
            return value
        return value

    def _format_value(self, value: Any) -> str:
        if isinstance(value, str):
            return f"\"{value}\""
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _extract_results(self, resp: Any) -> Tuple[List[Document], List[Optional[float]]]:
        documents: List[Document] = []
        scores: List[Optional[float]] = []
        raw = resp
        if isinstance(resp, dict) and "documents" in resp:
            raw = resp.get("documents")
        if not raw:
            return documents, scores
        items: List[Dict[str, Any]]
        if isinstance(raw, list) and raw and isinstance(raw[0], list):
            items = raw[0]
        elif isinstance(raw, list):
            items = raw
        else:
            return documents, scores
        for item in items:
            doc_payload = item.get("document") if isinstance(item, dict) else None
            if not isinstance(doc_payload, dict):
                doc_payload = item if isinstance(item, dict) else {}
            text = (
                doc_payload.get(self.text_field)
                or item.get("text")
                or item.get("Text")
                or ""
            )
            metadata = doc_payload.get(self.metadata_field) or {}
            for field in self.filter_fields:
                if field not in metadata and field in doc_payload:
                    metadata[field] = doc_payload.get(field)
            doc_id = doc_payload.get(self.id_field)
            if doc_id is not None and "id" not in metadata:
                metadata["id"] = doc_id
            score = None
            if isinstance(item, dict):
                score = item.get("score")
                if score is None:
                    score = item.get("Score")
                if score is None:
                    score = item.get("distance")
                if score is None:
                    score = item.get("Distance")
            documents.append(Document(page_content=text, metadata=metadata))
            scores.append(score)
        return documents, scores
