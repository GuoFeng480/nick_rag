-- =========================================================
-- 表名：rag_documents
-- 说明：RAG 系统中的“文档级元数据表”
--       用于管理多年份、多版本文档的业务事实信息
--       不存 chunk，不参与向量检索
-- =========================================================

CREATE TABLE rag_documents (
  id BIGINT PRIMARY KEY,
  -- 文档唯一标识
  -- 作为业务主键

  doc_type VARCHAR(50) NOT NULL,
  -- 文档类型
  -- 例如：travel_policy / hr_policy / faq
  -- 用于区分不同业务域的文档

  year INT NOT NULL,
  -- 文档适用年份
  -- 例如：2022 / 2023 / 2024
  -- RAG 查询时用于 metadata filter

  version INT NOT NULL,
  -- 同一年内的版本号
  -- 例如：1 / 2 / 3
  -- 只要求递增，不要求语义化

  status VARCHAR(20) NOT NULL,
  -- 文档状态
  -- active   : 当前生效版本
  -- inactive : 历史版本（仍保留，用于回溯）

  filename VARCHAR(255),
  -- 原始文件名
  -- 用于问题排查、溯源和人工确认

  vector_id VARCHAR(128),
  -- 文档对应的向量库 ID

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  -- 文档记录创建时间
  -- 表示“入系统时间”，不是文件发布时间
);