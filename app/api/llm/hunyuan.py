"""腾讯混元 LLM 客户端实现。

封装对话接口的请求与响应解析，提供文本输出能力。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

from app.api.llm.base_llm import BaseLLM, Message
from app.config.settings import Settings, get_settings


class HunyuanLLM(BaseLLM):
	"""混元 LLM 客户端。

	封装腾讯混元对话接口，提供文本结果与原始 JSON 输出。
	"""

	def __init__(self, settings: Optional[Settings] = None) -> None:
		"""初始化混元 LLM 客户端配置。

		参数:
			settings: 配置对象，包含密钥、地域、模型名、Endpoint。
		"""
		self.settings = settings or get_settings()
		cred = credential.Credential(
			self.settings.hunyuan_secret_id,
			self.settings.hunyuan_secret_key,
		)
		http_profile = HttpProfile()
		http_profile.endpoint = self.settings.hunyuan_endpoint
		client_profile = ClientProfile()
		client_profile.httpProfile = http_profile
		self.client = hunyuan_client.HunyuanClient(
			cred,
			self.settings.hunyuan_region,
			client_profile,
		)

	def chat(
		self,
		messages: List[Message],
		temperature: float = 0.7,
		max_tokens: int = 1024,
	) -> str:
		"""发送对话请求并返回文本结果。

		参数:
			messages: 对话消息列表。
			temperature: 采样温度。
			max_tokens: 最大输出长度。
		"""
		req = models.ChatCompletionsRequest()
		req.Model = self.settings.hunyuan_model
		req.Messages = [
			{"Role": m.get("role", "user"), "Content": m.get("content", "")}
			for m in messages
		]
		req.Temperature = temperature
		req.MaxTokens = max_tokens

		resp = self.client.ChatCompletions(req)
		if hasattr(resp, "Choices") and resp.Choices:
			return resp.Choices[0].Message.Content
		raise RuntimeError("Hunyuan response missing choices")

	def raw_chat(
		self,
		messages: List[Message],
		temperature: float = 0.7,
		max_tokens: int = 1024,
	) -> str:
		"""发送对话请求并返回原始 JSON 字符串。

		用于调试或保留模型返回的完整结构。
		"""
		req = models.ChatCompletionsRequest()
		req.Model = self.settings.hunyuan_model
		req.Messages = [
			{"Role": m.get("role", "user"), "Content": m.get("content", "")}
			for m in messages
		]
		req.Temperature = temperature
		req.MaxTokens = max_tokens
		resp = self.client.ChatCompletions(req)
		return resp.to_json_string()

