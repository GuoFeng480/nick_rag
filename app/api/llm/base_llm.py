"""
LLM 抽象接口定义。

统一对话输入与文本输出的调用规范。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


Message = Dict[str, str]


class BaseLLM(ABC):
	"""LLM 抽象基类。

	约定实现类需支持对话输入与文本输出。
	"""

	@abstractmethod
	def chat(self, messages: List[Message], **kwargs) -> str:
		"""执行多轮对话请求。

		参数:
			messages: 由 role/content 构成的消息列表。
			kwargs: 透传给底层实现的可选参数。
		"""
		raise NotImplementedError

	def completion(self, prompt: str, **kwargs) -> str:
		"""单轮补全接口封装为对话调用。

		参数:
			prompt: 用户输入。
			kwargs: 透传给 chat 的可选参数。
		"""
		return self.chat([{"role": "user", "content": prompt}], **kwargs)

