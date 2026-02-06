"""
配置加载与管理。

集中读取 .env 并提供应用级配置对象。
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.config.env_loader import get_bool, get_env, get_float, get_int, load_env


@dataclass(frozen=True)
class Settings:
	"""应用配置数据结构。

	集中管理 LLM、向量库、检索、预设问题匹配等配置。
	"""
	hunyuan_secret_id: str
	hunyuan_secret_key: str
	hunyuan_region: str
	hunyuan_model: str
	hunyuan_endpoint: str

	chroma_collection: str
	chroma_host: str
	chroma_port: int
	chroma_ssl: bool
	chroma_tenant: str
	chroma_database: str
	chroma_api_key: str
	chroma_auth_header: str
	preset_questions_collection: str
	preset_top_k: int
	preset_max_distance: float

	postgres_dsn: str

	hunyuan_embedding_model: str
	chunk_size: int
	chunk_overlap: int
	top_k: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	"""加载并缓存配置。

	说明:
		首次调用会读取 .env 并构建 Settings，后续复用缓存。
	"""
	load_env()
	return Settings(
		hunyuan_secret_id=get_env("HUNYUAN_SECRET_ID", required=True),
		hunyuan_secret_key=get_env("HUNYUAN_SECRET_KEY", required=True),
		hunyuan_region=get_env("HUNYUAN_REGION", default="ap-guangzhou"),
		hunyuan_model=get_env("HUNYUAN_MODEL", default="hunyuan-turbo"),
		hunyuan_endpoint=get_env("HUNYUAN_ENDPOINT", default="hunyuan.tencentcloudapi.com"),
		chroma_collection=get_env("CHROMA_COLLECTION", default="rag_default"),
		chroma_host=get_env("CHROMA_HOST", default=""),
		chroma_port=get_int("CHROMA_PORT", 8000),
		chroma_ssl=get_bool("CHROMA_SSL", False),
		chroma_tenant=get_env("CHROMA_TENANT", default=""),
		chroma_database=get_env("CHROMA_DATABASE", default=""),
		chroma_api_key=get_env("CHROMA_API_KEY", default=""),
		chroma_auth_header=get_env("CHROMA_AUTH_HEADER", default="Authorization"),
		preset_questions_collection=get_env(
			"PRESET_QUESTIONS_COLLECTION",
			default="preset_questions",
		),
		preset_top_k=get_int("PRESET_TOP_K", 1),
		preset_max_distance=get_float("PRESET_MAX_DISTANCE", 0.35),
		postgres_dsn=get_env(
			"POSTGRES_DSN",
			default="postgresql://postgres:postgres@localhost:5432/rag",
		),
		hunyuan_embedding_model=get_env(
			"HUNYUAN_EMBEDDING_MODEL",
			default="hunyuan-embedding",
		),
		chunk_size=get_int("CHUNK_SIZE", 800),
		chunk_overlap=get_int("CHUNK_OVERLAP", 120),
		top_k=get_int("TOP_K", 4),
	)

