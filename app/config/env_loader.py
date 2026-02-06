"""环境变量加载与类型转换工具。"""

from __future__ import annotations

import os
from typing import Optional


def load_env(path: Optional[str] = None) -> None:
	"""加载 .env 文件（如果可用）。

	参数:
		path: 可选 .env 路径，默认读取当前工作目录。
	"""
	try:
		from dotenv import load_dotenv
	except Exception:
		return

	load_dotenv(dotenv_path=path, override=False)


def get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
	"""获取环境变量字符串。

	参数:
		name: 环境变量名。
		default: 缺省值。
		required: 是否必须提供。
	"""
	value = os.getenv(name, default)
	if required and (value is None or value == ""):
		raise ValueError(f"Missing required env var: {name}")
	return "" if value is None else value


def get_int(name: str, default: int) -> int:
	"""获取整型环境变量。

	参数:
		name: 环境变量名。
		default: 缺省值。
	"""
	value = os.getenv(name)
	if value is None or value == "":
		return default
	return int(value)


def get_bool(name: str, default: bool = False) -> bool:
	"""获取布尔型环境变量。

	参数:
		name: 环境变量名。
		default: 缺省值。
	"""
	value = os.getenv(name)
	if value is None or value == "":
		return default
	return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_float(name: str, default: float) -> float:
	"""获取浮点型环境变量。

	参数:
		name: 环境变量名。
		default: 缺省值。
	"""
	value = os.getenv(name)
	if value is None or value == "":
		return default
	return float(value)

