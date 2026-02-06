"""RAG 对话编排引擎。"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from app.api.llm.base_llm import BaseLLM
from app.api.llm.hunyuan import HunyuanLLM
from app.config.settings import Settings, get_settings
from app.core.rag.retriever import VectorRetriever
from app.core.rag.prompts import (
	DEFAULT_HUMAN_PROMPT,
	DEFAULT_SYSTEM_PROMPT,
	QUESTION_REWRITE_PROMPT,
)


def _format_docs(docs: Iterable[Document]) -> str:
	"""将检索结果拼接为上下文字符串。"""
	parts = [doc.page_content for doc in docs]
	return "\n\n".join(parts) if parts else ""


class RAGEngine:
	"""RAG 对话编排引擎。

	负责检索增强生成与会话历史管理。
	"""

	def __init__(
		self,
		retriever: VectorRetriever,
		llm: Optional[BaseLLM] = None,
		settings: Optional[Settings] = None,
	) -> None:
		"""初始化对话编排依赖。"""
		self.settings = settings or get_settings()
		self.retriever = retriever
		self.llm = llm or HunyuanLLM(self.settings)
		self._history_store: Dict[str, BaseChatMessageHistory] = {}

	def _get_history(self, session_id: str) -> BaseChatMessageHistory:
		"""按会话 ID 获取消息历史。"""
		if session_id not in self._history_store:
			self._history_store[session_id] = InMemoryChatMessageHistory()
		return self._history_store[session_id]

	def _rewrite_question(
		self,
		question: str,
		history: BaseChatMessageHistory,
	) -> str:
		"""将上下文依赖问题改写为独立完整问题（最小实现）。"""
		if not history.messages:
			return question

		prompt = QUESTION_REWRITE_PROMPT.format(
			history=history,
			question=question,
		)

		rewritten = self.llm.completion(prompt)
		return rewritten.strip() or question

	def answer(
		self,
		question: str,
		session_id: str = "default",
		doc_filter: Optional[Dict[str, Any]] = None,
	) -> tuple[str, Dict[str, str]]:
		"""回答问题并返回结果与捕获信息。

		说明:
			在同一链路中捕获 prompt，避免重复构建。
		"""
		# 1) 准备 prompt 捕获容器，用于记录本次请求的最终 prompt 文本
		captured: Dict[str, str] = {"prompt": "", "session_id": session_id}

		# 2) 构建 prompt 模板：system/历史/human 三段
		#    - system: 全局约束与回答策略
		#    - history: 会话历史占位符
		#    - human: 注入 context 与 question
		prompt = ChatPromptTemplate.from_messages(
			[
				("system", DEFAULT_SYSTEM_PROMPT),
				MessagesPlaceholder(variable_name="history"),
				("human", DEFAULT_HUMAN_PROMPT),
			]
		)

		# 3) 构建检索函数：按过滤条件检索并拼接上下文, 获取会话历史，改写问题
		history = self._get_history(session_id)
		standalone_question = self._rewrite_question(question, history)

		def build_context(_: str) -> str:
			docs = self.retriever.search(
				standalone_question,
				filter=doc_filter,
			)
			return _format_docs(docs)

		# 4) 捕获 prompt：在链路中记录渲染后的 prompt 文本
		def capture_prompt(prompt_value):
			captured["prompt"] = prompt_value.to_string()
			return captured["prompt"]

		# 5) 组装链路：检索 -> prompt -> prompt文本 -> LLM -> 输出
		base_chain = (
			{
				"context": RunnableLambda(build_context),
				"question": RunnablePassthrough(),
			}
			| prompt
			| RunnableLambda(capture_prompt)
			| RunnableLambda(lambda text: self.llm.completion(text))
			| StrOutputParser()
		)

		# 6) 注入会话历史管理，让多轮对话共享历史
		chain = RunnableWithMessageHistory(
			base_chain,
			self._get_history,
			input_messages_key="question",
			history_messages_key="history",
		)

		# 7) 执行链路并返回答案
		answer = chain.invoke(
			question,
			config={"configurable": {"session_id": session_id}},
		)

		# 8) 返回答案与捕获到的信息
		return answer, captured
