"""
file_utils 模块
功能：file utils
"""

from __future__ import annotations

from typing import List

from unstructured.partition.pdf import partition_pdf


def load_pdf_texts(file_path: str) -> List[str]:
	"""解析 PDF 并返回文本列表。

	参数:
		file_path: PDF 文件路径。
	返回:
		按顺序提取的文本列表。
	"""
	elements = partition_pdf(filename=file_path)
	return [el.text for el in elements if getattr(el, "text", None)]

