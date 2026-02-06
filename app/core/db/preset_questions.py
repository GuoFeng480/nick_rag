"""预设问题模型与访问层。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.config.settings import Settings, get_settings
from app.core.db.database import get_session
from app.core.db.models import Base


class PresetQuestion(Base):
    """预设问题表模型。

    用于保存预设问答、分类与向量库映射。
    """

    __tablename__ = "preset_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    vector_id: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())


class PresetQuestionStore:
    """预设问题访问层。

    提供创建、查询、筛选与向量 ID 更新能力。
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """初始化访问层。

        参数:
            settings: 配置对象。
        """
        self.settings = settings or get_settings()

    def create_question(
        self,
        question: str,
        answer: Optional[str] = None,
        category: Optional[str] = None,
        status: str = "active",
        vector_id: Optional[str] = None,
    ) -> PresetQuestion:
        """新增预设问题记录。

        参数:
            question: 预设问题文本。
            answer: 预设问题答案。
            category: 业务分类。
            status: 状态。
            vector_id: 向量库 ID。
        """
        with get_session(self.settings) as session:
            item = PresetQuestion(
                question=question,
                answer=answer,
                category=category,
                status=status,
                vector_id=vector_id,
            )
            session.add(item)
            session.flush()
            session.refresh(item)
            return item

    def get_question(self, question_id: int) -> Optional[PresetQuestion]:
        """按 ID 获取预设问题。

        参数:
            question_id: 预设问题 ID。
        """
        with get_session(self.settings) as session:
            return session.get(PresetQuestion, question_id)

    def get_active_question(self, question_id: int) -> Optional[PresetQuestion]:
        """按 ID 获取生效预设问题。

        参数:
            question_id: 预设问题 ID。
        """
        stmt = (
            select(PresetQuestion)
            .where(PresetQuestion.id == question_id)
            .where(PresetQuestion.status == "active")
            .limit(1)
        )
        with get_session(self.settings) as session:
            return session.execute(stmt).scalars().first()

    def list_active(self, category: Optional[str] = None) -> List[PresetQuestion]:
        """获取生效的预设问题列表。

        参数:
            category: 可选分类过滤。
        """
        stmt = select(PresetQuestion).where(PresetQuestion.status == "active")
        if category:
            stmt = stmt.where(PresetQuestion.category == category)
        with get_session(self.settings) as session:
            return list(session.execute(stmt).scalars().all())

    def update_vector_id(self, question_id: int, vector_id: str) -> None:
        """更新向量 ID。

        参数:
            question_id: 预设问题 ID。
            vector_id: 向量库 ID。
        """
        with get_session(self.settings) as session:
            item = session.get(PresetQuestion, question_id)
            if not item:
                return
            item.vector_id = vector_id
