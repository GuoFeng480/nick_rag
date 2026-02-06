"""RAG 对外入口模块。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.config.settings import Settings, get_settings
from app.core.db.user_questions import UserQuestionStore
from app.core.db.preset_questions import PresetQuestionStore
from app.core.rag.metadata_helper import MetadataHelper
from app.core.rag.rag_engine import RAGEngine
from app.core.rag.retriever import VectorRetriever


class ChatService:
	"""RAG 对外入口服务。

	负责预设问题命中、RAG 对话编排与问答记录。
	"""

	def __init__(
		self,
		settings: Optional[Settings] = None,
		retriever: Optional[VectorRetriever] = None,
		rag_engine: Optional[RAGEngine] = None,
		preset_retriever: Optional[VectorRetriever] = None,
		preset_store: Optional[PresetQuestionStore] = None,
		question_store: Optional[UserQuestionStore] = None,
	) -> None:
		"""初始化对外入口依赖。

		说明:
			允许注入检索器与引擎，便于测试或替换实现。
		"""
		self.settings = settings or get_settings()
		self.retriever = retriever or VectorRetriever.from_settings(self.settings)
		self.rag_engine = rag_engine or RAGEngine(
			retriever=self.retriever,
			settings=self.settings,
		)
		self.preset_retriever = preset_retriever or VectorRetriever.from_settings(
			self.settings,
			collection_name=self.settings.preset_questions_collection,
		)
		self.preset_store = preset_store or PresetQuestionStore(self.settings)
		self.question_store = question_store or UserQuestionStore(self.settings)

	def answer(
		self,
		question: str,
		session_id: str = "default",
	) -> str:
		"""
		基于用户问题进行元数据匹配，如年份版本等，
		先预设问题命中，再走 RAG 生成，并记录问答。

		参数:
			question: 用户问题。
			session_id: 会话 ID（用于上下文历史）。
		"""
		# 1) 从问题中抽取过滤条件（年份/版本等）
		analysis = MetadataHelper.build_filter(question)
		doc_filter = analysis["filter"]
		# 2) 初始化进度日志结构
		process_track: Dict[str, Any] = {
			"doc_filter": doc_filter,
			"config": {
				"top_k": self.settings.top_k,
				"chroma_collection": self.settings.chroma_collection,
				"preset_top_k": self.settings.preset_top_k,
				"preset_max_distance": self.settings.preset_max_distance,
				"preset_collection": self.settings.preset_questions_collection,
			},
			"preset": {"matched": False},
			"rag": None,
		}
		# 3) 记录问题基础信息
		record = self.question_store.create_question(
			question=question,
			session_id=session_id,
			user_id=None,
			process_track=None,
		)
		# 4) 先尝试预设问题匹配
		preset_match = self.preset_retriever.match_preset(
			question,
			preset_store=self.preset_store,
		)
		if preset_match:
			# 5) 命中预设问题，写入进度与回答
			process_track["preset"] = {
				"matched": True,
				"preset_id": preset_match.get("preset_id"),
				"score": preset_match.get("score"),
			}
			self.question_store.update_answer(
				record.id,
				answer=str(preset_match.get("answer", "")),
				answer_source="preset",
				process_track=process_track,
			)
			return str(preset_match.get("answer", ""))
		# 6) 未命中预设问题，记录 RAG prompt 与会话信息
		# 7) 进入 RAG 生成，并在链路中捕获 prompt
		answer, captured = self.rag_engine.answer(
			question,
			session_id=session_id,
			doc_filter=doc_filter or None,
		)
		process_track["rag"] = {
			"captured": captured,
			"llm_model": self.settings.hunyuan_model,
		}
		self.question_store.update_answer(
			record.id,
			answer=answer,
			answer_source="rag",
			process_track=process_track,
		)
		return answer


