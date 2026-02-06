-- =========================================================
-- 表名：rag_user_questions
-- 说明：用户问题与回答记录表
--       用于问题追踪、预设更新与分析
-- =========================================================

CREATE TABLE rag_user_questions (
  id BIGSERIAL PRIMARY KEY,
  -- 主键

  session_id VARCHAR(100),
  -- 会话 ID

  user_id VARCHAR(100),
  -- 用户 ID

  question TEXT NOT NULL,
  -- 用户问题

  answer TEXT,
  -- 模型回答

  process_track JSONB,
  -- 过程日志

  answer_source VARCHAR(20),
  -- 回答来源：preset/rag

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  -- 创建时间

  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  -- 更新时间
);
