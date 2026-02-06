"""SQLAlchemy 会话与引擎初始化。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import Settings, get_settings


def _build_engine(dsn: str):
    """根据 DSN 创建 SQLAlchemy 引擎。

    参数:
        dsn: 数据库连接串。
    """
    return create_engine(dsn, pool_pre_ping=True)


def get_engine(settings: Optional[Settings] = None):
    """获取数据库引擎实例。

    参数:
        settings: 配置对象。
    """
    cfg = settings or get_settings()
    return _build_engine(cfg.postgres_dsn)


def get_session_factory(settings: Optional[Settings] = None):
    """获取会话工厂。

    参数:
        settings: 配置对象。
    """
    engine = get_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session(settings: Optional[Settings] = None) -> Iterator[Session]:
    """获取数据库会话上下文。

    说明:
        使用上下文管理器自动提交或回滚事务。
    """
    session_factory = get_session_factory(settings)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
