"""HTTP API 入口。"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.core.chat import ChatService


app = FastAPI(title="RAG Service", version="1.0.0")
chat_service = ChatService()


class RAGRequest(BaseModel):
	"""RAG 请求体。"""

	question: str = Field(..., description="用户问题")


class RAGResponse(BaseModel):
	"""RAG 响应体。"""

	answer: str
	session_id: str


@app.post("/api/rag", response_model=RAGResponse)
def rag_answer(payload: RAGRequest) -> RAGResponse:
	"""RAG 问答入口。"""
	session_id = "default"
	answer = chat_service.answer(
		payload.question,
		session_id=session_id,
	)
	return RAGResponse(answer=answer, session_id=session_id)


@app.get("/healthz")
def healthz() -> Dict[str, str]:
	"""健康检查。"""
	return {"status": "ok"}

