"""SQLAlchemy 模型基础定义。

定义全局 Base，供各模型继承。
"""

from __future__ import annotations

from sqlalchemy.orm import declarative_base

Base = declarative_base()
