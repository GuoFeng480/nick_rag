"""预设问题向量化与匹配组件。"""

from __future__ import annotations

from typing import Optional

from app.api.embedding.hunyuan import get_embeddings
from app.api.vector_db.base_vector import BaseVector
from app.config.settings import Settings, get_settings
from app.core.db.preset_questions import PresetQuestionStore
from app.config.vector_schema import preset_questions as preset_table


class PresetEmbedder:
    """预设问题向量化封装。

    负责同步预设问题到向量库。
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        vector_db: Optional[BaseVector] = None,
        preset_store: Optional[PresetQuestionStore] = None,
    ) -> None:
        """初始化预设问题组件。

        参数:
            settings: 配置对象。
            vector_db: 向量库写入实现。
            preset_store: 预设问题存储。
        """
        self.settings = settings or get_settings()
        if vector_db is None:
            collection_name = preset_table.COLLECTION_NAME
            self.vector_db = BaseVector.from_settings(
                embedding_function=get_embeddings(self.settings),
                settings=self.settings,
                collection_name=collection_name,
                table_config=preset_table,
            )
        else:
            self.vector_db = vector_db
        self.preset_store = preset_store or PresetQuestionStore(self.settings)

    def sync_preset_questions(self, category: Optional[str] = None) -> int:
        """同步预设问题到向量库。

        参数:
            category: 可选分类过滤。
        返回:
            同步的记录数量。
        """
        items = self.preset_store.list_active(category=category)
        if not items:
            return 0
        texts = [item.question for item in items]
        metadatas = [
            {"preset_id": item.id, "category": item.category}
            for item in items
        ]
        ids = [item.vector_id or f"preset-{item.id}" for item in items]
        returned_ids = self.vector_db.add_texts(
            texts,
            metadatas=metadatas,
            ids=ids,
        )
        for item, vector_id in zip(items, returned_ids):
            self.preset_store.update_vector_id(item.id, vector_id)
        return len(items)

