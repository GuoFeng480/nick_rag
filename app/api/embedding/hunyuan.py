"""混元向量化客户端实现。"""

from __future__ import annotations

from typing import List, Optional

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

from app.api.embedding.base_embedding import BaseEmbedding
from app.config.settings import Settings, get_settings


class HunyuanEmbeddings(BaseEmbedding):
    """混元 Embedding 客户端。

    负责封装腾讯混元向量化接口，提供批量/单条向量生成。
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """初始化混元 Embedding 客户端配置。

        参数:
            settings: 配置对象，包含密钥、地域、模型名、Endpoint。
        """
        self.settings = settings or get_settings()
        cred = credential.Credential(
            self.settings.hunyuan_secret_id,
            self.settings.hunyuan_secret_key,
        )
        http_profile = HttpProfile()
        http_profile.endpoint = self.settings.hunyuan_endpoint
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        self.client = hunyuan_client.HunyuanClient(
            cred,
            self.settings.hunyuan_region,
            client_profile,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化。

        参数:
            texts: 待向量化的文本列表。
        返回:
            向量列表，与输入文本一一对应。
        """
        if not texts:
            return []
        return self._embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        """单条查询向量化。

        参数:
            text: 查询文本。
        返回:
            单条向量。
        """
        return self._embeddings([text])[0]

    def _embeddings(self, texts: List[str]) -> List[List[float]]:
        """调用混元 Embedding 接口并解析响应。

        说明:
            根据混元返回结构兼容 Data 或 Embeddings 字段。
        """
        req = models.EmbeddingsRequest()
        req.Model = self.settings.hunyuan_embedding_model
        req.Input = texts
        resp = self.client.Embeddings(req)
        if hasattr(resp, "Data") and resp.Data:
            return [item.Embedding for item in resp.Data]
        if hasattr(resp, "Embeddings") and resp.Embeddings:
            return resp.Embeddings
        raise RuntimeError("Hunyuan embeddings response missing data")


def get_embeddings(settings: Optional[Settings] = None) -> BaseEmbedding:
    """获取混元 Embedding 客户端实例。

    参数:
        settings: 可选配置对象。
    """
    return HunyuanEmbeddings(settings=settings)
