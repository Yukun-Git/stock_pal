-- ============================================================================
-- 股票数据缓存模块 (PostgreSQL)
-- ============================================================================
-- 功能: 缓存从AkShare获取的股票历史行情数据，减少API调用次数
-- 使用: CacheService (backend/app/services/cache_service.py)
-- 数据库: PostgreSQL 15+
-- 创建时间: 2024-10-30
-- 最后更新: 2025-11-16
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 表: stock_data
-- 说明: 存储股票历史行情数据（OHLCV + 其他指标）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_data (
    -- 主键字段
    symbol VARCHAR(20) NOT NULL,       -- 股票代码（如：000001, 600000, 00700.HK）
    date DATE NOT NULL,                -- 交易日期（YYYY-MM-DD）

    -- 价格字段（OHLC）
    open NUMERIC(10, 4),               -- 开盘价
    high NUMERIC(10, 4),               -- 最高价
    low NUMERIC(10, 4),                -- 最低价
    close NUMERIC(10, 4),              -- 收盘价

    -- 成交量和金额
    volume BIGINT,                     -- 成交量（股）
    amount NUMERIC(20, 2),             -- 成交额（元）

    -- 其他指标
    amplitude NUMERIC(10, 4),          -- 振幅（%）
    pct_change NUMERIC(10, 4),         -- 涨跌幅（%）
    change NUMERIC(10, 4),             -- 涨跌额（元）
    turnover NUMERIC(10, 4),           -- 换手率（%）

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 数据写入时间

    -- 主键约束
    PRIMARY KEY (symbol, date)
);

-- 添加表注释
COMMENT ON TABLE stock_data IS '股票历史行情数据缓存';
COMMENT ON COLUMN stock_data.symbol IS '股票代码';
COMMENT ON COLUMN stock_data.date IS '交易日期';
COMMENT ON COLUMN stock_data.volume IS '成交量（股）';
COMMENT ON COLUMN stock_data.amount IS '成交额（元）';

-- ----------------------------------------------------------------------------
-- 索引: idx_symbol_date
-- 说明: 加速按股票代码和日期查询
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_stock_data_symbol_date
ON stock_data(symbol, date);

-- 可选索引：如果经常按日期范围查询所有股票
CREATE INDEX IF NOT EXISTS idx_stock_data_date
ON stock_data(date);

-- ----------------------------------------------------------------------------
-- 表: data_sync_log
-- 说明: 记录每只股票的数据同步状态，用于增量更新
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_sync_log (
    -- 主键
    symbol VARCHAR(20) PRIMARY KEY,    -- 股票代码

    -- 数据范围
    first_date DATE,                   -- 最早数据日期
    last_date DATE,                    -- 最新数据日期
    record_count INTEGER,              -- 记录总数

    -- 元数据
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 最后更新时间
);

-- 添加表注释
COMMENT ON TABLE data_sync_log IS '股票数据同步日志';
COMMENT ON COLUMN data_sync_log.first_date IS '缓存中最早的数据日期';
COMMENT ON COLUMN data_sync_log.last_date IS '缓存中最新的数据日期';

-- ----------------------------------------------------------------------------
-- 触发器: 自动更新 updated_at
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_data_sync_log_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_data_sync_log_timestamp
BEFORE UPDATE ON data_sync_log
FOR EACH ROW
EXECUTE FUNCTION update_data_sync_log_timestamp();

-- ----------------------------------------------------------------------------
-- 示例查询
-- ----------------------------------------------------------------------------

-- 1. 查询某只股票的历史数据
-- SELECT * FROM stock_data
-- WHERE symbol = '000001'
-- AND date >= '2023-01-01'
-- ORDER BY date;

-- 2. 查看缓存统计
-- SELECT
--     symbol,
--     first_date,
--     last_date,
--     record_count,
--     updated_at
-- FROM data_sync_log
-- ORDER BY updated_at DESC;

-- 3. 清理过期数据（删除1年前的数据）
-- DELETE FROM stock_data
-- WHERE date < CURRENT_DATE - INTERVAL '1 year';

-- 4. 查看数据库大小
-- SELECT
--     COUNT(DISTINCT symbol) as stock_count,
--     COUNT(*) as total_records,
--     MIN(date) as earliest_date,
--     MAX(date) as latest_date
-- FROM stock_data;

-- 5. 查看表空间使用情况
-- SELECT
--     pg_size_pretty(pg_total_relation_size('stock_data')) as total_size,
--     pg_size_pretty(pg_relation_size('stock_data')) as table_size,
--     pg_size_pretty(pg_indexes_size('stock_data')) as indexes_size;

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 定期清理：建议保留最近2-3年数据，删除更早的历史数据
-- 2. 数据完整性：通过 data_sync_log 表检查数据是否连续
-- 3. 索引维护：数据量大时考虑 VACUUM 和 REINDEX
-- 4. 备份策略：使用 pg_dump 定期备份数据库
-- 5. 分区表：数据量超过1000万条时考虑按年份分区
-- ============================================================================
