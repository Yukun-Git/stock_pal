-- ============================================================================
-- 自选股管理系统 MVP - 数据库表结构 (PostgreSQL)
-- ============================================================================
-- 功能: 自选股管理、分组管理
-- 数据库: PostgreSQL 15+
-- 状态: 开发中
-- 创建时间: 2025-11-19
-- 设计文档: doc/design/watchlist_system_design.md
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 表: watchlist_groups
-- 说明: 自选股分组表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlist_groups (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 外键
    user_id VARCHAR(36) NOT NULL,      -- 用户ID（UUID格式，引用 users.id）

    -- 分组信息
    name VARCHAR(50) NOT NULL,         -- 分组名称
    color VARCHAR(20),                 -- 颜色标签（hex或预设值）
    sort_order INTEGER NOT NULL DEFAULT 0,  -- 排序顺序（越小越靠前）

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT fk_watchlist_groups_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_user_group_name UNIQUE (user_id, name),  -- 同一用户下分组名称唯一
    CONSTRAINT chk_sort_order CHECK (sort_order >= 0),
    CONSTRAINT chk_name_not_empty CHECK (length(name) > 0)
);

-- 添加表注释
COMMENT ON TABLE watchlist_groups IS '自选股分组表';
COMMENT ON COLUMN watchlist_groups.id IS '分组ID（自增）';
COMMENT ON COLUMN watchlist_groups.user_id IS '所属用户ID（UUID）';
COMMENT ON COLUMN watchlist_groups.name IS '分组名称';
COMMENT ON COLUMN watchlist_groups.color IS '颜色标签（用于UI展示）';
COMMENT ON COLUMN watchlist_groups.sort_order IS '排序顺序（越小越靠前）';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_watchlist_groups_user_id
    ON watchlist_groups(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_groups_user_name
    ON watchlist_groups(user_id, name);

-- 创建触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_watchlist_groups_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_watchlist_groups_timestamp
BEFORE UPDATE ON watchlist_groups
FOR EACH ROW
EXECUTE FUNCTION update_watchlist_groups_timestamp();

-- ----------------------------------------------------------------------------
-- 表: watchlist_stocks
-- 说明: 自选股表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlist_stocks (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 外键
    user_id VARCHAR(36) NOT NULL,      -- 所属用户ID（UUID）
    stock_code VARCHAR(20) NOT NULL,   -- 股票代码（如600000）
    stock_name VARCHAR(50) NOT NULL,   -- 股票名称（如浦发银行）
    group_id BIGINT,                   -- 所属分组ID（NULL=未分类）

    -- 用户备注
    note TEXT,                         -- 个人备注

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT fk_watchlist_stocks_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_watchlist_stocks_group FOREIGN KEY (group_id)
        REFERENCES watchlist_groups(id) ON DELETE SET NULL,  -- 删除分组时，股票不删除，group_id设为NULL
    CONSTRAINT uk_user_stock_code UNIQUE (user_id, stock_code),  -- 同一用户不能重复添加同一股票
    CONSTRAINT chk_stock_code_format CHECK (stock_code ~ '^[0-9]{6}$'),  -- 6位数字股票代码
    CONSTRAINT chk_stock_name_not_empty CHECK (length(stock_name) > 0)
);

-- 添加表注释
COMMENT ON TABLE watchlist_stocks IS '自选股表';
COMMENT ON COLUMN watchlist_stocks.id IS '自选股记录ID（自增）';
COMMENT ON COLUMN watchlist_stocks.user_id IS '所属用户ID（UUID）';
COMMENT ON COLUMN watchlist_stocks.stock_code IS '股票代码（6位数字）';
COMMENT ON COLUMN watchlist_stocks.stock_name IS '股票名称';
COMMENT ON COLUMN watchlist_stocks.group_id IS '所属分组ID（NULL表示未分类）';
COMMENT ON COLUMN watchlist_stocks.note IS '用户个人备注';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_watchlist_stocks_user_id
    ON watchlist_stocks(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_stocks_group_id
    ON watchlist_stocks(group_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_stocks_user_code
    ON watchlist_stocks(user_id, stock_code);
CREATE INDEX IF NOT EXISTS idx_watchlist_stocks_created_at
    ON watchlist_stocks(created_at);  -- 用于按添加时间排序

-- 创建触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_watchlist_stocks_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_watchlist_stocks_timestamp
BEFORE UPDATE ON watchlist_stocks
FOR EACH ROW
EXECUTE FUNCTION update_watchlist_stocks_timestamp();

-- ============================================================================
-- 初始化数据：为每个用户创建默认分组"未分类"
-- ============================================================================
-- 注意：这个脚本会在用户注册时由应用层触发，这里只是示例

-- 为现有用户创建默认分组（如果不存在）
INSERT INTO watchlist_groups (user_id, name, color, sort_order)
SELECT
    u.id,
    '未分类',
    '#999999',
    0
FROM users u
WHERE NOT EXISTS (
    SELECT 1
    FROM watchlist_groups wg
    WHERE wg.user_id = u.id AND wg.name = '未分类'
);

-- ============================================================================
-- 示例查询
-- ============================================================================

-- 1. 获取用户的所有自选股及分组信息
-- SELECT
--     ws.id,
--     ws.stock_code,
--     ws.stock_name,
--     ws.note,
--     ws.created_at,
--     wg.id as group_id,
--     wg.name as group_name,
--     wg.color as group_color
-- FROM watchlist_stocks ws
-- LEFT JOIN watchlist_groups wg ON ws.group_id = wg.id
-- WHERE ws.user_id = 'user_uuid_here'
-- ORDER BY ws.created_at DESC;

-- 2. 获取某个分组下的所有股票
-- SELECT
--     stock_code,
--     stock_name,
--     note,
--     created_at
-- FROM watchlist_stocks
-- WHERE user_id = 'user_uuid_here'
--   AND group_id = 1
-- ORDER BY created_at DESC;

-- 3. 获取用户的所有分组及每组股票数量
-- SELECT
--     wg.id,
--     wg.name,
--     wg.color,
--     wg.sort_order,
--     COUNT(ws.id) as stock_count
-- FROM watchlist_groups wg
-- LEFT JOIN watchlist_stocks ws ON wg.id = ws.group_id
-- WHERE wg.user_id = 'user_uuid_here'
-- GROUP BY wg.id, wg.name, wg.color, wg.sort_order
-- ORDER BY wg.sort_order;

-- 4. 检查股票是否在用户自选股中
-- SELECT
--     id,
--     group_id,
--     (SELECT name FROM watchlist_groups WHERE id = ws.group_id) as group_name
-- FROM watchlist_stocks ws
-- WHERE user_id = 'user_uuid_here'
--   AND stock_code = '600000'
-- LIMIT 1;

-- 5. 统计用户自选股数据
-- SELECT
--     COUNT(*) as total_stocks,
--     COUNT(DISTINCT group_id) as total_groups,
--     MIN(created_at) as first_added_at,
--     MAX(created_at) as last_added_at
-- FROM watchlist_stocks
-- WHERE user_id = 'user_uuid_here';

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 自动管理：updated_at 字段通过触发器自动更新
-- 2. 级联删除：删除用户时，自动删除其所有分组和自选股
-- 3. 默认分组：删除分组时，分组内股票的 group_id 设为 NULL（移至"未分类"）
-- 4. 唯一性：同一用户下，分组名称唯一，股票代码唯一
-- 5. 数据验证：股票代码必须为6位数字，分组名称不能为空
-- 6. 索引优化：已为常用查询创建索引，提升性能
-- ============================================================================
