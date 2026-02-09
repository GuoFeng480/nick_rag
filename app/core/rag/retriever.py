"""RAG 向量检索封装。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from app.api.vector_db.base_vector import BaseVector
from app.config.settings import Settings, get_settings
from app.api.embedding.base_embedding import BaseEmbedding
from app.api.embedding.hunyuan import get_embeddings
from app.core.db.preset_questions import PresetQuestionStore
from app.config.vector_schema import documents as documents_table


class VectorRetriever:
	"""向量检索器。

	负责连接向量库并提供检索能力。
	"""

	def __init__(
		self,
		vector_db: BaseVector,
		settings: Optional[Settings] = None,
	) -> None:
		"""初始化检索器。

		参数:
			vector_db: 向量库接口实现。
			settings: 配置对象。
		"""
		self.vector_db = vector_db
		self.settings = settings or get_settings()

	@classmethod
	def from_settings(
		cls,
		settings: Optional[Settings] = None,
		collection_name: Optional[str] = None,
		embedding: Optional[BaseEmbedding] = None,
		table_config: Optional[Any] = None,
	) -> "VectorRetriever":
		"""根据配置构建检索器。

		参数:
			settings: 配置对象。
			collection_name: 可选集合名。
			embedding: 可选 Embedding 实现。
		"""
		cfg = settings or get_settings()
		embeddings = embedding or get_embeddings(cfg)
		collection = collection_name or documents_table.COLLECTION_NAME
		resolved_table = table_config or documents_table
		vector_db = BaseVector.from_settings(
			embedding_function=embeddings,
			settings=cfg,
			collection_name=collection,
			table_config=resolved_table,
		)
		return cls(vector_db=vector_db, settings=cfg)

	def search(
		self,
		query: str,
		k: Optional[int] = None,
		filter: Optional[Dict[str, Any]] = None,
	) -> List[Document]:
		"""执行向量检索。

		参数:
			query: 查询文本。
			k: 返回数量。
			filter: 元数据过滤条件。
		"""
		top_k = k or self.settings.top_k
		return self.vector_db.similarity_search(query, k=top_k, filter=filter)

	def search_with_score(
		self,
		query: str,
		k: Optional[int] = None,
		filter: Optional[Dict[str, Any]] = None,
	) -> List[Any]:
		"""执行向量检索并返回得分。

		说明:
			得分为向量库返回的距离或相似度。
		"""
		top_k = k or self.settings.top_k
		return self.vector_db.similarity_search_with_score(query, k=top_k, filter=filter)

	def match_preset(
		self,
		question: str,
		preset_store: PresetQuestionStore,
	) -> Optional[Dict[str, Any]]:
		"""匹配预设问题并返回详细信息。

		说明:
			使用向量检索命中预设问题，并根据距离阈值判定。
			返回包含答案、预设问题 ID 与匹配得分的字典。
		"""
		results = self.search_with_score(
			question,
			k=self.settings.preset_top_k,
		)
		if not results:
			return None
		doc, score = results[0]
		if score is None or score > self.settings.preset_max_distance:
			return None
		preset_id = doc.metadata.get("preset_id") or doc.metadata.get("id")
		if preset_id is None:
			return None
		item = preset_store.get_active_question(int(preset_id))
		if not item or not item.answer:
			return None
		return {
			"answer": item.answer,
			"preset_id": int(preset_id),
			"score": score,
		}

