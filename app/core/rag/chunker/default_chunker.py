"""默认切分器实现。

该模块提供一个可直接用于生产的默认切分器实现，
核心职责是：
1) 将 Unstructured 解析得到的元素转换为 LangChain Document；
2) 使用可配置的分隔策略把长文本切成语义块；
3) 在不影响切分结果的前提下，尽量保留结构化元数据。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import Settings, get_settings
from app.core.rag.chunker.base_chunker import Chunker


class DefaultChunker(Chunker):
    """基于 RecursiveCharacterTextSplitter 的切分器。

    设计目标：
    - 使用可配置的 chunk_size / chunk_overlap 进行块级切分；
    - 通过正则分隔符优先级让切分尽量发生在自然边界；
    - 保留元素级元数据，便于检索后回溯来源与版面信息。
    """

    def __init__(self, settings: Settings) -> None:
        # 保存配置，以便在调用方需要时可访问或调试。
        self.settings = settings
        # 递归切分器会优先使用 separators 中靠前的分隔符进行切分，
        # 当无法满足 chunk_size 时再逐级退化到更细粒度的分隔符。
        self.splitter = RecursiveCharacterTextSplitter(
            # 单个 chunk 的目标长度。
            chunk_size=self.settings.chunk_size,
            # 相邻 chunk 的重叠长度，用于保留跨块上下文。
            chunk_overlap=self.settings.chunk_overlap,
            separators=[
                # 段落级分隔：连续空行是最优切分边界。
                "\\n\\n+",
                # 行级分隔：退化到单行换行。
                "\\n",
                # 句末分隔：中文句号/问号/感叹号。
                "[。！？]",
                # 分号：次级句内停顿。
                "[；;]",
                # 逗号：更细粒度的语义分割。
                "[，,]",
                # 空白：最后兜底，确保任何文本可被切开。
                "\\s+",
            ],
            # 分隔符是正则表达式而非字面字符串。
            is_separator_regex=True,
        )

    @classmethod
    def from_settings(cls, settings: Optional[Settings] = None) -> "DefaultChunker":
        """根据配置创建切分器。

        当调用方未显式传入 settings 时，
        使用全局配置加载器获取默认配置。
        """
        cfg = settings or get_settings()
        return cls(cfg)

    def chunk_elements(self, elements: List[Any], base_metadata: Dict[str, Any]) -> List[Document]:
        """将结构化元素切分为块。

        处理流程：
        1) 读取元素文本；
        2) 合并元素级元数据到基础元数据；
        3) 构建 Document 列表；
        4) 交给 splitter 完成最终切分。
        """
        # 先将元素转换为 Document，便于统一调用 split_documents。
        documents: List[Document] = []
        for element in elements:
            # Unstructured 的元素通常提供 text 属性；若为空则跳过。
            text = getattr(element, "text", None)
            if not text:
                continue
            # 每个元素独立复制 base_metadata，防止相互污染。
            meta = dict(base_metadata)
            # 元素类型通常来自 element.category（如 Title/Paragraph/Table）。
            meta["element_type"] = getattr(element, "category", None)
            # 元数据里常见的页码字段来自 element.metadata.page_number。
            if hasattr(element, "metadata"):
                meta["page_number"] = getattr(element.metadata, "page_number", None)
            # 将元素文本与元数据封装成 Document。
            documents.append(Document(page_content=text, metadata=meta))
        # 使用 LangChain 的 split_documents 做最终切分，返回 Document 列表。
        return self.splitter.split_documents(documents)
