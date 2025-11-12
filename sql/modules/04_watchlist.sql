-- ============================================================================
-- 观察列表与提醒模块（未来功能）
-- ============================================================================
-- 功能: 用户自选股、分组管理、价格提醒
-- 状态: 设计中（根据 PRD 需求）
-- 创建时间: 2025-11-12
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 表: watchlists
-- 说明: 观察列表（自选股分组）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlists (
    -- 主键
    id VARCHAR(36) PRIMARY KEY,        -- 列表ID

    -- 外键
    user_id VARCHAR(36) NOT NULL,      -- 用户ID

    -- 列表信息
    name VARCHAR(50) NOT NULL,         -- 列表名称
    description TEXT,                  -- 描述
    color VARCHAR(20),                 -- 颜色标记
    sort_order INTEGER DEFAULT 0,      -- 排序

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_user (user_id)
);

-- ----------------------------------------------------------------------------
-- 表: watchlist_items
-- 说明: 观察列表项目（具体股票）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlist_items (
    -- 主键
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 外键
    watchlist_id VARCHAR(36) NOT NULL, -- 列表ID
    symbol VARCHAR(20) NOT NULL,       -- 股票代码
    market_id VARCHAR(10),             -- 市场标识

    -- 备注信息
    note TEXT,                         -- 关注理由
    tags VARCHAR(200),                 -- 标签（逗号分隔）

    -- 目标价位
    target_buy_price DECIMAL(10, 4),   -- 目标买入价
    target_sell_price DECIMAL(10, 4),  -- 目标卖出价
    stop_loss_price DECIMAL(10, 4),    -- 止损价

    -- 执行记录
    buy_executed BOOLEAN DEFAULT FALSE,     -- 是否已买入
    buy_executed_at DATETIME,               -- 买入时间
    buy_price DECIMAL(10, 4),               -- 实际买入价
    sell_executed BOOLEAN DEFAULT FALSE,    -- 是否已卖出
    sell_executed_at DATETIME,              -- 卖出时间
    sell_price DECIMAL(10, 4),              -- 实际卖出价

    -- 排序
    sort_order INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,

    -- 唯一约束
    UNIQUE KEY unique_watchlist_symbol (watchlist_id, symbol),

    -- 索引
    INDEX idx_watchlist (watchlist_id),
    INDEX idx_symbol (symbol)
);

-- ----------------------------------------------------------------------------
-- 表: price_alerts
-- 说明: 价格提醒规则
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS price_alerts (
    -- 主键
    id VARCHAR(36) PRIMARY KEY,        -- 提醒ID

    -- 外键
    user_id VARCHAR(36) NOT NULL,      -- 用户ID
    symbol VARCHAR(20) NOT NULL,       -- 股票代码
    market_id VARCHAR(10),             -- 市场标识

    -- 提醒条件
    alert_type VARCHAR(20) NOT NULL,   -- 类型：price_above, price_below, pct_change, volume
    condition_value DECIMAL(10, 4),    -- 条件值
    condition_operator VARCHAR(10),    -- 操作符：>, <, >=, <=

    -- 提醒设置
    notify_channel VARCHAR(20) DEFAULT 'email',  -- 通知渠道：email, sms, push
    message TEXT,                      -- 自定义消息

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,    -- 是否激活
    is_triggered BOOLEAN DEFAULT FALSE,     -- 是否已触发
    triggered_at TIMESTAMP,            -- 触发时间
    triggered_price DECIMAL(10, 4),    -- 触发时价格

    -- 频率控制
    max_trigger_count INTEGER DEFAULT 1,       -- 最大触发次数
    trigger_count INTEGER DEFAULT 0,           -- 已触发次数
    cooldown_minutes INTEGER DEFAULT 60,       -- 冷却时间（分钟）

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,              -- 过期时间

    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_user (user_id),
    INDEX idx_symbol (symbol),
    INDEX idx_active (is_active),
    INDEX idx_expires (expires_at)
);

-- ----------------------------------------------------------------------------
-- 表: alert_logs
-- 说明: 提醒触发日志
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alert_logs (
    -- 主键
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 外键
    alert_id VARCHAR(36) NOT NULL,     -- 提醒ID
    user_id VARCHAR(36) NOT NULL,      -- 用户ID

    -- 触发信息
    symbol VARCHAR(20) NOT NULL,       -- 股票代码
    triggered_at TIMESTAMP NOT NULL,   -- 触发时间
    trigger_price DECIMAL(10, 4),      -- 触发价格
    trigger_condition TEXT,            -- 触发条件描述

    -- 发送状态
    notify_channel VARCHAR(20),        -- 通知渠道
    send_status VARCHAR(20),           -- 发送状态：pending, sent, failed
    sent_at TIMESTAMP,                 -- 发送时间
    error_message TEXT,                -- 错误信息

    -- 索引
    INDEX idx_alert (alert_id),
    INDEX idx_user (user_id),
    INDEX idx_triggered (triggered_at)
);

-- ============================================================================
-- SQLite 适配版本
-- ============================================================================

-- CREATE TABLE IF NOT EXISTS watchlists (
--     id TEXT PRIMARY KEY,
--     user_id TEXT NOT NULL,
--     name TEXT NOT NULL,
--     description TEXT,
--     color TEXT,
--     sort_order INTEGER DEFAULT 0,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
-- );

-- CREATE INDEX IF NOT EXISTS idx_watchlists_user ON watchlists(user_id);

-- CREATE TABLE IF NOT EXISTS watchlist_items (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     watchlist_id TEXT NOT NULL,
--     symbol TEXT NOT NULL,
--     market_id TEXT,
--     note TEXT,
--     tags TEXT,
--     target_buy_price REAL,
--     target_sell_price REAL,
--     stop_loss_price REAL,
--     buy_executed INTEGER DEFAULT 0,
--     buy_executed_at DATETIME,
--     buy_price REAL,
--     sell_executed INTEGER DEFAULT 0,
--     sell_executed_at DATETIME,
--     sell_price REAL,
--     sort_order INTEGER DEFAULT 0,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
--     UNIQUE(watchlist_id, symbol)
-- );

-- CREATE INDEX IF NOT EXISTS idx_watchlist_items_list ON watchlist_items(watchlist_id);
-- CREATE INDEX IF NOT EXISTS idx_watchlist_items_symbol ON watchlist_items(symbol);

-- ============================================================================
-- 示例查询
-- ============================================================================

-- 1. 查询用户的观察列表
-- SELECT
--     w.id,
--     w.name,
--     COUNT(wi.id) as stock_count
-- FROM watchlists w
-- LEFT JOIN watchlist_items wi ON w.id = wi.watchlist_id
-- WHERE w.user_id = 'user_123'
-- GROUP BY w.id
-- ORDER BY w.sort_order;

-- 2. 查询列表中的股票
-- SELECT
--     symbol,
--     market_id,
--     note,
--     target_buy_price,
--     target_sell_price,
--     buy_executed,
--     created_at
-- FROM watchlist_items
-- WHERE watchlist_id = 'list_001'
-- ORDER BY sort_order;

-- 3. 查询激活的价格提醒
-- SELECT
--     symbol,
--     alert_type,
--     condition_value,
--     notify_channel
-- FROM price_alerts
-- WHERE user_id = 'user_123'
-- AND is_active = TRUE
-- AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
-- ORDER BY created_at DESC;

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 定期清理过期的提醒记录
-- 2. alert_logs 表需定期归档（如保留3个月）
-- 3. 触发提醒时需检查冷却时间
-- 4. 股票代码变更时需要同步更新
-- ============================================================================
