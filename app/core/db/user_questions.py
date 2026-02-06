"""用户问题与回答记录模型与访问层。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import BigInteger, DateTime, String, Text, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.config.settings import Settings, get_settings
from app.core.db.database import get_session
from app.core.db.models import Base


class UserQuestion(Base):
    """用户问题记录表模型。"""

    __tablename__ = "rag_user_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text)
    process_track: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    answer_source: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserQuestionStore:
    """用户问题访问层。"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """初始化访问层。

        参数:
            settings: 配置对象。
        """
        self.settings = settings or get_settings()

    def create_question(
        self,
        question: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        process_track: Optional[Dict[str, Any]] = None,
    ) -> UserQuestion:
        """新增用户问题记录。

        参数:
            question: 用户问题。
            session_id: 会话 ID。
            user_id: 用户 ID。
            process_track: 过程日志。
        """
        with get_session(self.settings) as session:
            item = UserQuestion(
                question=question,
                session_id=session_id,
                user_id=user_id,
                process_track=process_track,
            )
            session.add(item)
            session.flush()
            session.refresh(item)
            return item

    def update_answer(
        self,
        question_id: int,
        answer: str,
        answer_source: Optional[str] = None,
        process_track: Optional[Dict[str, Any]] = None,
    ) -> None:
        """更新回答与来源。

        参数:
            question_id: 问题记录 ID。
            answer: 回答内容。
            answer_source: 回答来源。
            process_track: 过程日志。
        """
        with get_session(self.settings) as session:
            item = session.get(UserQuestion, question_id)
            if not item:
                return
            item.answer = answer
            item.answer_source = answer_source
            if process_track is not None:
                item.process_track = process_track
            session.flush()

    def get_question(self, question_id: int) -> Optional[UserQuestion]:
        """按 ID 获取记录。"""
        stmt = select(UserQuestion).where(UserQuestion.id == question_id).limit(1)
        with get_session(self.settings) as session:
            return session.execute(stmt).scalars().first()
