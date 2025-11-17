-- ============================================================================
-- 观察列表与提醒模块 (PostgreSQL)
-- ============================================================================
-- 功能: 用户自选股、分组管理、价格提醒
-- 数据库: PostgreSQL 15+
-- 状态: 设计中（根据 PRD 需求）
-- 创建时间: 2025-11-12
-- 最后更新: 2025-11-16
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
    CONSTRAINT fk_watchlists_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE
);

-- 添加表注释
COMMENT ON TABLE watchlists IS '观察列表（自选股分组）';
COMMENT ON COLUMN watchlists.id IS '列表ID';
COMMENT ON COLUMN watchlists.user_id IS '用户ID';
COMMENT ON COLUMN watchlists.name IS '列表名称';
COMMENT ON COLUMN watchlists.sort_order IS '排序顺序';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_watchlists_user
ON watchlists(user_id);

-- 创建触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_watchlists_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_watchlists_timestamp
BEFORE UPDATE ON watchlists
FOR EACH ROW
EXECUTE FUNCTION update_watchlists_timestamp();

-- ----------------------------------------------------------------------------
-- 表: watchlist_items
-- 说明: 观察列表项目（具体股票）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlist_items (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 外键
    watchlist_id VARCHAR(36) NOT NULL, -- 列表ID
    symbol VARCHAR(20) NOT NULL,       -- 股票代码
    market_id VARCHAR(10),             -- 市场标识

    -- 备注信息
    note TEXT,                         -- 关注理由
    tags VARCHAR(200),                 -- 标签（逗号分隔）

    -- 目标价位
    target_buy_price NUMERIC(10, 4),   -- 目标买入价
    target_sell_price NUMERIC(10, 4),  -- 目标卖出价
    stop_loss_price NUMERIC(10, 4),    -- 止损价

    -- 执行记录
    buy_executed BOOLEAN DEFAULT FALSE,     -- 是否已买入
    buy_executed_at TIMESTAMP,              -- 买入时间
    buy_price NUMERIC(10, 4),               -- 实际买入价
    sell_executed BOOLEAN DEFAULT FALSE,    -- 是否已卖出
    sell_executed_at TIMESTAMP,             -- 卖出时间
    sell_price NUMERIC(10, 4),              -- 实际卖出价

    -- 排序
    sort_order INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束和唯一约束
    CONSTRAINT fk_watchlist_items_watchlist FOREIGN KEY (watchlist_id)
        REFERENCES watchlists(id) ON DELETE CASCADE,
    CONSTRAINT uq_watchlist_items_watchlist_symbol UNIQUE (watchlist_id, symbol)
);

-- 添加表注释
COMMENT ON TABLE watchlist_items IS '观察列表项目（具体股票）';
COMMENT ON COLUMN watchlist_items.id IS '项目ID';
COMMENT ON COLUMN watchlist_items.watchlist_id IS '所属列表ID';
COMMENT ON COLUMN watchlist_items.buy_executed IS '是否已买入';
COMMENT ON COLUMN watchlist_items.sell_executed IS '是否已卖出';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_watchlist_items_watchlist
ON watchlist_items(watchlist_id);

CREATE INDEX IF NOT EXISTS idx_watchlist_items_symbol
ON watchlist_items(symbol);

-- 创建触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_watchlist_items_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_watchlist_items_timestamp
BEFORE UPDATE ON watchlist_items
FOR EACH ROW
EXECUTE FUNCTION update_watchlist_items_timestamp();

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
    condition_value NUMERIC(10, 4),    -- 条件值
    condition_operator VARCHAR(10),    -- 操作符：>, <, >=, <=

    -- 提醒设置
    notify_channel VARCHAR(20) DEFAULT 'email',  -- 通知渠道：email, sms, push
    message TEXT,                      -- 自定义消息

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,    -- 是否激活
    is_triggered BOOLEAN DEFAULT FALSE,     -- 是否已触发
    triggered_at TIMESTAMP,            -- 触发时间
    triggered_price NUMERIC(10, 4),    -- 触发时价格

    -- 频率控制
    max_trigger_count INTEGER DEFAULT 1,       -- 最大触发次数
    trigger_count INTEGER DEFAULT 0,           -- 已触发次数
    cooldown_minutes INTEGER DEFAULT 60,       -- 冷却时间（分钟）

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,              -- 过期时间

    -- 外键约束
    CONSTRAINT fk_price_alerts_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_alert_type CHECK (alert_type IN ('price_above', 'price_below', 'pct_change', 'volume'))
);

-- 添加表注释
COMMENT ON TABLE price_alerts IS '价格提醒规则';
COMMENT ON COLUMN price_alerts.id IS '提醒ID';
COMMENT ON COLUMN price_alerts.alert_type IS '提醒类型：price_above(价格高于), price_below(价格低于), pct_change(百分比变化), volume(成交量)';
COMMENT ON COLUMN price_alerts.is_active IS '是否激活';
COMMENT ON COLUMN price_alerts.is_triggered IS '是否已触发';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_price_alerts_user
ON price_alerts(user_id);

CREATE INDEX IF NOT EXISTS idx_price_alerts_symbol
ON price_alerts(symbol);

CREATE INDEX IF NOT EXISTS idx_price_alerts_active
ON price_alerts(is_active);

CREATE INDEX IF NOT EXISTS idx_price_alerts_expires
ON price_alerts(expires_at);

-- 创建触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_price_alerts_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_price_alerts_timestamp
BEFORE UPDATE ON price_alerts
FOR EACH ROW
EXECUTE FUNCTION update_price_alerts_timestamp();

-- ----------------------------------------------------------------------------
-- 表: alert_logs
-- 说明: 提醒触发日志
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alert_logs (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 外键
    alert_id VARCHAR(36) NOT NULL,     -- 提醒ID
    user_id VARCHAR(36) NOT NULL,      -- 用户ID

    -- 触发信息
    symbol VARCHAR(20) NOT NULL,       -- 股票代码
    triggered_at TIMESTAMP NOT NULL,   -- 触发时间
    trigger_price NUMERIC(10, 4),      -- 触发价格
    trigger_condition TEXT,            -- 触发条件描述

    -- 发送状态
    notify_channel VARCHAR(20),        -- 通知渠道
    send_status VARCHAR(20),           -- 发送状态：pending, sent, failed
    sent_at TIMESTAMP,                 -- 发送时间
    error_message TEXT,                -- 错误信息

    -- 外键约束和校验
    CONSTRAINT fk_alert_logs_alert FOREIGN KEY (alert_id)
        REFERENCES price_alerts(id) ON DELETE CASCADE,
    CONSTRAINT fk_alert_logs_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_send_status CHECK (send_status IN ('pending', 'sent', 'failed'))
);

-- 添加表注释
COMMENT ON TABLE alert_logs IS '提醒触发日志';
COMMENT ON COLUMN alert_logs.send_status IS '发送状态：pending(待发送), sent(已发送), failed(发送失败)';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_alert_logs_alert
ON alert_logs(alert_id);

CREATE INDEX IF NOT EXISTS idx_alert_logs_user
ON alert_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_alert_logs_triggered
ON alert_logs(triggered_at);

-- ============================================================================
-- 示例查询
-- ============================================================================

-- 1. 查询用户的观察列表及其中的股票数量
-- SELECT
--     w.id,
--     w.name,
--     COUNT(wi.id) as stock_count
-- FROM watchlists w
-- LEFT JOIN watchlist_items wi ON w.id = wi.watchlist_id
-- WHERE w.user_id = 'user_123'
-- GROUP BY w.id, w.name
-- ORDER BY w.sort_order;

-- 2. 查询列表中的股票及其目标价位
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

-- 3. 查询激活且未过期的价格提醒
-- SELECT
--     symbol,
--     alert_type,
--     condition_value,
--     notify_channel,
--     is_active
-- FROM price_alerts
-- WHERE user_id = 'user_123'
-- AND is_active = TRUE
-- AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
-- ORDER BY created_at DESC;

-- 4. 查询提醒触发日志
-- SELECT
--     al.symbol,
--     al.trigger_price,
--     al.triggered_at,
--     al.send_status,
--     pa.alert_type
-- FROM alert_logs al
-- LEFT JOIN price_alerts pa ON al.alert_id = pa.id
-- WHERE al.user_id = 'user_123'
-- ORDER BY al.triggered_at DESC
-- LIMIT 100;

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 自动管理：updated_at 字段通过触发器自动更新
-- 2. 过期提醒：定期清理 expires_at 已过期的提醒记录
-- 3. 日志归档：alert_logs 表需定期归档（如保留3个月）
-- 4. 触发冷却：触发提醒时需检查 cooldown_minutes 冷却时间
-- 5. 数据一致性：删除 watchlist 会自动删除关联的 watchlist_items
-- 6. 索引优化：根据查询模式添加组合索引提升性能
-- ============================================================================
