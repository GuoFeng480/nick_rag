"""基于迁移表结构的文档元数据访问层。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.config.settings import Settings, get_settings
from app.core.db.database import get_session
from app.core.db.models import Base


class RagDocument(Base):
    """文档元数据表模型。

    用于记录文档级信息与向量库的映射。
    """

    __tablename__ = "rag_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String(255))
    vector_id: Mapped[Optional[str]] = mapped_column(String(128))
    effective_from: Mapped[Optional[str]] = mapped_column(String(20))
    effective_to: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())


class RagDocumentStore:
    """文档元数据访问层。

    提供新增、更新与查询接口。
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """初始化存储访问层。

        参数:
            settings: 配置对象。
        """
        self.settings = settings or get_settings()

    def upsert_document(
        self,
        doc_id: int,
        doc_type: str,
        year: int,
        version: int,
        status: str,
        filename: Optional[str] = None,
        vector_id: Optional[str] = None,
        effective_from: Optional[str] = None,
        effective_to: Optional[str] = None,
    ) -> None:
        """新增或更新文档元数据。

        参数:
            doc_id: 文档 ID。
            doc_type: 文档类型。
            year: 文档年份。
            version: 文档版本。
            status: 文档状态。
            filename: 文件名。
            vector_id: 向量库 ID。
        """
        with get_session(self.settings) as session:
            existing = session.get(RagDocument, doc_id)
            if existing:
                existing.doc_type = doc_type
                existing.year = year
                existing.version = version
                existing.status = status
                existing.filename = filename
                existing.vector_id = vector_id
                existing.effective_from = effective_from
                existing.effective_to = effective_to
                return

            doc = RagDocument(
                id=doc_id,
                doc_type=doc_type,
                year=year,
                version=version,
                status=status,
                filename=filename,
                vector_id=vector_id,
                effective_from=effective_from,
                effective_to=effective_to,
            )
            session.add(doc)

    def get_document(self, doc_id: int) -> Optional[RagDocument]:
        """按文档 ID 获取记录。

        参数:
            doc_id: 文档 ID。
        """
        with get_session(self.settings) as session:
            return session.get(RagDocument, doc_id)

    def get_active_document(self, doc_type: str, year: int) -> Optional[RagDocument]:
        """获取指定类型年份的最新生效版本。

        参数:
            doc_type: 文档类型。
            year: 文档年份。
        """
        stmt = (
            select(RagDocument)
            .where(RagDocument.doc_type == doc_type)
            .where(RagDocument.year == year)
            .where(RagDocument.status == "active")
            .order_by(RagDocument.version.desc())
            .limit(1)
        )
        with get_session(self.settings) as session:
            return session.execute(stmt).scalars().first()
