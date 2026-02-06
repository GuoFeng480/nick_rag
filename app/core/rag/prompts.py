"""RAG 提示词模板。

包含系统提示词与用户提示词模板，可按业务扩展。
"""

DEFAULT_SYSTEM_PROMPT = (
	"你是一个专业的中文助手。请基于提供的上下文回答问题。"
	"如果上下文不相关或没有答案，请直接说明不知道。"
)

DEFAULT_HUMAN_PROMPT = """问题：
{question}

上下文：
{context}
"""

QUESTION_REWRITE_PROMPT = """
You are a query rewriter.

Given the conversation history and the latest user question,
rewrite the question so that it is fully self-contained.
If the question is already self-contained, return it as-is.

Conversation history:
{history}

User question:
{question}

Standalone question:
""".strip()
