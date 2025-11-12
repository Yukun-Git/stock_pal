-- ============================================================================
-- 用户管理模块（预留）
-- ============================================================================
-- 功能: 用户认证、授权、个人设置
-- 状态: 预留（当前版本未实现用户系统）
-- 创建时间: 2025-11-12
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
    last_login_at TIMESTAMP,

    -- 索引
    INDEX idx_username (username),
    INDEX idx_email (email)
);

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
    ip_address VARCHAR(45),                 -- IP地址
    user_agent TEXT,                        -- 浏览器UA

    -- 有效期
    expires_at TIMESTAMP NOT NULL,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_token (token)
);

-- ----------------------------------------------------------------------------
-- 表: user_preferences
-- 说明: 用户偏好设置
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_preferences (
    -- 主键
    user_id VARCHAR(36) PRIMARY KEY,   -- 用户ID

    -- 偏好设置（JSON）
    preferences JSON,                  -- 包括：默认市场、语言、时区、通知设置等

    -- 时间戳
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================================
-- SQLite 适配版本
-- ============================================================================

-- CREATE TABLE IF NOT EXISTS users (
--     id TEXT PRIMARY KEY,
--     username TEXT UNIQUE NOT NULL,
--     email TEXT UNIQUE NOT NULL,
--     password_hash TEXT NOT NULL,
--     salt TEXT,
--     nickname TEXT,
--     avatar_url TEXT,
--     is_active INTEGER DEFAULT 1,
--     is_verified INTEGER DEFAULT 0,
--     is_premium INTEGER DEFAULT 0,
--     role TEXT DEFAULT 'user',
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     last_login_at TIMESTAMP
-- );

-- CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 当前版本为单用户模式，暂不启用此模块
-- 2. 未来多用户版本时再激活
-- 3. 密码使用 bcrypt 或 argon2 哈希
-- 4. Session 需定期清理过期记录
-- ============================================================================
