-- =========================================================
-- 表名：preset_questions
-- 说明：预设问题表
--       用于保存预设问题与向量库映射
-- =========================================================

CREATE TABLE preset_questions (
  id BIGSERIAL PRIMARY KEY,
  -- 预设问题主键

  question TEXT NOT NULL,
  -- 预设问题文本

  answer TEXT,
  -- 预设问题答案

  category VARCHAR(100),
  -- 业务分类

  status VARCHAR(20) NOT NULL DEFAULT 'active',
  -- 状态：active/inactive

  vector_id VARCHAR(128),
  -- 向量库中的向量 ID

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  -- 创建时间
);
