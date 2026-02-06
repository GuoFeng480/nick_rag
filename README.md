# nick_rag

项目简介：基于Python的RAG项目，集成LLM、RAG、Agent能力，对接企业CRM和知识库

## 快速启动

1. 创建并激活虚拟环境
   python3 -m venv .venv
   source .venv/bin/activate
2. 安装依赖：pip install -r requirements.txt
   可能会缺少libheif系统级包，来源于unstructured[pdf]依赖，需要先行安装
   mac下(proxy):brew install libheif
3. 配置.env文件（填写密钥等信息）
4. 启动服务：uvicorn app.main:app --host 0.0.0.0 --port 8000

## API

- POST /api/rag
    - 请求体：
        - question: 用户问题（必填）
        - 说明：目前仅支持 question，session_id 由服务端固定为 default。
    - 响应体：
        - answer: 模型回答
        - session_id: 会话ID

## 文档入库（指定目录的 PDF/DOCX）

说明：只会解析并向量化指定目录下的 PDF/DOCX 文件。
入库时必须传入文档元数据，用于写入向量 metadata（doc_type/year/version/status/filename）。

```bash
python scripts/ingest_documents.py /path/to/docs \
	--doc-type travel_policy --year 2024 --version 1 --status active
```

## 预设问题向量化

说明：预设问题必须先写入数据库表 preset_questions，才能进行向量化与回写 vector_id。

```bash
python scripts/ingest_presets.py
```

## 数据表

- rag_documents：文档级元数据表（含 vector_id）
- preset_questions：预设问题表（含 answer、vector_id）
- rag_user_questions：用户问题与回答记录表

## 核心

PDF / DOCX
↓
Unstructured.partition
→ Element（带类型 + 页码 + 弱结构）
↓
Chunker（控制的核心）
→ Chunk（语义完整 + 结构 metadata）
↓
Embedding（中文友好）
↓
Vector DB（metadata 可过滤）
↓
RAG Retriever (向量搜索排序打分)
