"""
向量库抽象接口定义。

统一写入与相似度检索的能力。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional


class BaseVector(ABC):
	"""向量库抽象基类。

	约定实现类支持写入文本向量、检索相似文本。
	"""

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

