"""
向量库抽象接口定义。

统一写入与相似度检索的能力。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Type

from app.api.embedding.base_embedding import BaseEmbedding
from app.config.settings import Settings, get_settings


class BaseVector(ABC):
	"""向量库抽象基类。

	约定实现类支持写入文本向量、检索相似文本。
	"""

	_registry: Dict[str, Type["BaseVector"]] = {}

	@classmethod
	def register_backend(cls, name: str, backend_cls: Type["BaseVector"]) -> None:
		"""注册向量库实现，支持可插拔选择。"""
		normalized = (name or "").strip().lower()
		if not normalized:
			raise ValueError("backend name is required")
		cls._registry[normalized] = backend_cls

	@classmethod
	def _ensure_backend_registered(cls, name: str) -> None:
		if name in cls._registry:
			return
		if name == "tencent":
			from app.api.vector_db import tencent_client  # noqa: F401
			return
		if name == "chroma":
			from app.api.vector_db import chroma_client  # noqa: F401
			return

	@abstractmethod
	def add_texts(
		self,
		texts: Iterable[str],
		metadatas: Optional[List[Dict[str, Any]]] = None,
		ids: Optional[List[str]] = None,
	) -> List[str]:
		"""写入文本向量并返回 ID 列表。

		参数:
			texts: 文本列表。
			metadatas: 每条文本对应的元数据。
			ids: 自定义 ID 列表。
		"""
		raise NotImplementedError

	@abstractmethod
	def similarity_search(
		self,
		query: str,
		k: int = 4,
		filter: Optional[Dict[str, Any]] = None,
	) -> List[Any]:
		"""相似度检索。

		参数:
			query: 查询文本。
			k: 返回数量。
			filter: 元数据过滤条件。
		"""
		raise NotImplementedError

	@abstractmethod
	def similarity_search_with_score(
		self,
		query: str,
		k: int = 4,
		filter: Optional[Dict[str, Any]] = None,
	) -> List[Any]:
		"""相似度检索并返回得分。

		说明:
			得分含义由底层向量库决定（如距离/相似度）。
		"""
		raise NotImplementedError

	@classmethod
	def from_settings(
		cls,
		embedding_function: BaseEmbedding,
		settings: Optional[Settings] = None,
		collection_name: Optional[str] = None,
		table_config: Optional[Any] = None,
	) -> "BaseVector":
		"""根据配置创建向量库实例。

		说明:
			通过 VECTOR_DB_BACKEND 选择具体实现，默认使用 Chroma。
		"""
		cfg = settings or get_settings()
		backend = (cfg.vector_db_backend or "chroma").strip().lower()
		cls._ensure_backend_registered(backend)
		if backend not in cls._registry:
			raise ValueError(f"Unknown vector db backend: {backend}")
		backend_cls = cls._registry[backend]
		return backend_cls(
			embedding_function=embedding_function,
			settings=cfg,
			collection_name=collection_name,
			table_config=table_config,
		)

