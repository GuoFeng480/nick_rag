"""预设问题集合的向量字段与索引配置常量。"""

COLLECTION_NAME = "preset_questions"

ID_FIELD = "id"
VECTOR_FIELD = "vector"
TEXT_FIELD = "text"
METADATA_FIELD = "metadata"

# 向量库可过滤的字段列表（用于检索条件）。
FILTER_FIELDS = [
    "preset_id",
    "category",
]

# 需要强制转为数值的字段（便于范围过滤/排序）。
NUMERIC_FIELDS = [
    "preset_id",
]

DIMENSION = 0

INDEX_TYPE = "HNSW"
METRIC_TYPE = "COSINE"
HNSW_M = 32
HNSW_EF_CONSTRUCTION = 400
HNSW_EF_SEARCH = 200

SHARD = 1
REPLICAS = 1
DESCRIPTION = ""
