"""根据问题抽取检索元数据过滤条件。"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List


TIME_KEYWORDS: Dict[str, List[str]] = {
    "current": [
        "当前", "现在", "目前", "现行", "最新", "最新版",
        "生效中", "在用的", "今年", "本年度", "当年",
    ],
    "last_year": [
        "去年", "上一年", "去年同期", "上一年度",
        "去年版", "旧版", "老版本", "之前一年",
    ],
    "year_before_last": [
        "前年",
    ],
    "historical": [
        "以前", "历史", "老政策", "早期", "原来", "最早", "旧政策",
    ],
    "recent_two_years": [
        "近两年", "过去两年",
    ],
    "recent_three_years": [
        "近三年", "过去三年",
    ],
    "compare": [
        "相比", "对比", "区别", "变化", "差异",
        "有什么不同", "改了什么", "调整了什么", "和",
    ],
}


class MetadataHelper:
    """问题元数据解析器。

    根据自然语言问题抽取年份与版本信息，生成向量检索过滤条件。
    """

    _YEAR_PATTERN = re.compile(r"(19\d{2}|20\d{2})")
    _VERSION_PATTERN = re.compile(r"(?:\bv|版本|第)\s*(\d+)")

    @classmethod
    def build_filter(cls, question: str) -> Dict[str, Any]:
        """从问题中构建过滤条件。

        参数:
            question: 用户问题。
        返回:
            包含过滤字典的结构化结果。
        """
        years = cls._extract_years(question)
        versions = cls._extract_versions(question)
        doc_filter: Dict[str, Any] = {}
        if years:
            doc_filter["year"] = {"$in": years}
        if versions:
            doc_filter["version"] = {"$in": versions}
        return {"filter": doc_filter}

    @classmethod
    def _extract_years(cls, question: str) -> List[int]:
        """抽取年份列表。"""
        years = {int(value) for value in cls._YEAR_PATTERN.findall(question)}
        current_year = datetime.now().year
        if cls._contains_any(question, TIME_KEYWORDS.get("current", [])):
            years.add(current_year)
        if cls._contains_any(question, TIME_KEYWORDS.get("last_year", [])):
            years.add(current_year - 1)
        if cls._contains_any(question, TIME_KEYWORDS.get("year_before_last", [])):
            years.add(current_year - 2)
        if cls._contains_any(question, TIME_KEYWORDS.get("compare", [])):
            years.update([current_year - 1, current_year])
        if cls._contains_any(question, TIME_KEYWORDS.get("historical", [])):
            years.update([current_year - 2, current_year - 1, current_year])
        if cls._contains_any(question, TIME_KEYWORDS.get("recent_two_years", [])):
            years.update([current_year - 1, current_year])
        if cls._contains_any(question, TIME_KEYWORDS.get("recent_three_years", [])):
            years.update([current_year - 2, current_year - 1, current_year])

        return sorted(years)

    @classmethod
    def _extract_versions(cls, question: str) -> List[int]:
        """抽取版本号列表。"""
        versions = {int(value) for value in cls._VERSION_PATTERN.findall(question)}
        return sorted(versions)

    @classmethod
    def _contains_any(cls, question: str, keywords: List[str]) -> bool:
        """判断问题中是否包含任意关键词。"""
        return any(key in question for key in keywords)


