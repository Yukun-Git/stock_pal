-- ============================================================================
-- 用户管理模块 (PostgreSQL) - 预留
-- ============================================================================
-- 功能: 用户认证、授权、个人设置
-- 数据库: PostgreSQL 15+
-- 状态: 预留（当前版本未实现用户系统）
-- 创建时间: 2025-11-12
-- 最后更新: 2025-11-16
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 表: users
-- 说明: 用户基本信息
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    -- 主键
    id VARCHAR(36) PRIMARY KEY,        -- 用户ID（UUID）

    -- 认证信息
    username VARCHAR(50) UNIQUE NOT NULL,   -- 用户名
    email VARCHAR(100) UNIQUE NOT NULL,     -- 邮箱
    password_hash VARCHAR(255) NOT NULL,    -- 密码哈希
    salt VARCHAR(50),                       -- 盐值

    -- 个人信息
    nickname VARCHAR(50),              -- 昵称
    avatar_url VARCHAR(255),           -- 头像URL

    -- 账户状态
    is_active BOOLEAN DEFAULT TRUE,    -- 是否激活
    is_verified BOOLEAN DEFAULT FALSE, -- 邮箱是否验证
    is_premium BOOLEAN DEFAULT FALSE,  -- 是否付费用户

    -- 权限
    role VARCHAR(20) DEFAULT 'user',   -- 角色（user, admin）

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- 添加表注释
COMMENT ON TABLE users IS '用户基本信息表';
COMMENT ON COLUMN users.password_hash IS '使用 bcrypt 或 argon2 哈希的密码';
COMMENT ON COLUMN users.role IS '用户角色: user(普通用户) 或 admin(管理员)';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username
ON users(username);

CREATE INDEX IF NOT EXISTS idx_users_email
ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_created_at
ON users(created_at);

-- 创建触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_users_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_users_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_users_timestamp();

-- ----------------------------------------------------------------------------
-- 表: user_sessions
-- 说明: 用户会话管理
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_sessions (
    -- 主键
    session_id VARCHAR(64) PRIMARY KEY,     -- 会话ID

    -- 外键
    user_id VARCHAR(36) NOT NULL,           -- 用户ID

    -- 会话信息
    token VARCHAR(255) UNIQUE NOT NULL,     -- JWT Token
    ip_address VARCHAR(45),                 -- IP地址（支持IPv6）
    user_agent TEXT,                        -- 浏览器UA

    -- 有效期
    expires_at TIMESTAMP NOT NULL,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

-- 添加表注释
COMMENT ON TABLE user_sessions IS '用户会话管理表';
COMMENT ON COLUMN user_sessions.token IS 'JWT 令牌';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_sessions_user
ON user_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_user_sessions_token
ON user_sessions(token);

CREATE INDEX IF NOT EXISTS idx_user_sessions_expires
ON user_sessions(expires_at);

-- ----------------------------------------------------------------------------
-- 表: user_preferences
-- 说明: 用户偏好设置
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_preferences (
    -- 主键
    user_id VARCHAR(36) PRIMARY KEY,   -- 用户ID

    -- 偏好设置（JSONB）
    preferences JSONB,                 -- 包括：默认市场、语言、时区、通知设置等

    -- 时间戳
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    CONSTRAINT fk_user_preferences_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

-- 添加表注释
COMMENT ON TABLE user_preferences IS '用户偏好设置表';
COMMENT ON COLUMN user_preferences.preferences IS 'JSONB格式存储用户偏好配置';

-- 创建 JSONB 索引
CREATE INDEX IF NOT EXISTS idx_user_preferences_jsonb
ON user_preferences USING GIN (preferences);

-- 创建触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_user_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_preferences_timestamp
BEFORE UPDATE ON user_preferences
FOR EACH ROW
EXECUTE FUNCTION update_user_preferences_timestamp();

-- ----------------------------------------------------------------------------
-- 示例查询
-- ----------------------------------------------------------------------------

-- 1. 创建新用户
-- INSERT INTO users (id, username, email, password_hash, nickname)
-- VALUES ('uuid-here', 'demo_user', 'demo@stockpal.com', 'hashed_password', 'Demo');

-- 2. 查询用户及其偏好
-- SELECT u.*, up.preferences
-- FROM users u
-- LEFT JOIN user_preferences up ON u.id = up.user_id
-- WHERE u.username = 'demo_user';

-- 3. 清理过期会话
-- DELETE FROM user_sessions
-- WHERE expires_at < CURRENT_TIMESTAMP;

-- 4. 查询活跃用户（最近30天登录）
-- SELECT username, email, last_login_at
-- FROM users
-- WHERE last_login_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
-- ORDER BY last_login_at DESC;

-- 5. 查询用户偏好中的特定设置
-- SELECT user_id, preferences->>'language' as language
-- FROM user_preferences
-- WHERE preferences->>'language' = 'zh-CN';

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 当前版本为单用户模式，暂不启用此模块
-- 2. 未来多用户版本时再激活
-- 3. 密码使用 bcrypt (成本因子12+) 或 argon2 哈希
-- 4. Session 需定期清理过期记录（使用 cron 或 pg_cron）
-- 5. 用户敏感信息需加密存储
-- 6. 定期备份用户数据
-- 7. 实施用户数据访问审计
-- ============================================================================
