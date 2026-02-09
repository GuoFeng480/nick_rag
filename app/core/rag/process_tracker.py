"""RAG 请求链路过程追踪。"""

from __future__ import annotations

from typing import Any, Dict

from app.config.settings import Settings


class ProcessTracker:
    """构建并更新过程追踪结构。"""

    def __init__(self, settings: Settings, documents_table: Any, preset_table: Any) -> None:
        self.settings = settings
        self.documents_table = documents_table
        self.preset_table = preset_table

    def build(self, doc_filter: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "doc_filter": doc_filter,
            "config": {
                "top_k": self.settings.top_k,
                "documents_collection": self.documents_table.COLLECTION_NAME,
                "preset_top_k": self.settings.preset_top_k,
                "preset_max_distance": self.settings.preset_max_distance,
                "preset_collection": self.preset_table.COLLECTION_NAME,
            },
            "preset": {"matched": False},
            "rag": None,
        }

    def record_preset_match(self, process_track: Dict[str, Any], preset_match: Dict[str, Any]) -> None:
        process_track["preset"] = {
            "matched": True,
            "preset_id": preset_match.get("preset_id"),
            "score": preset_match.get("score"),
        }

    def record_rag(self, process_track: Dict[str, Any], captured: Any, llm_model: str) -> None:
        process_track["rag"] = {
            "captured": captured,
            "llm_model": llm_model,
        }
