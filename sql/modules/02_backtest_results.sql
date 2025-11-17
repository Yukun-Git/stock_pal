-- ============================================================================
-- 回测结果存储模块 (PostgreSQL)
-- ============================================================================
-- 功能: 存储回测运行记录、交易明细、权益曲线等结果数据
-- 使用: BacktestService V2 (未来实现)
-- 数据库: PostgreSQL 15+
-- 创建时间: 2025-11-12
-- 最后更新: 2025-11-16
-- 状态: 设计中（根据 doc/backlog/回测结果存储与历史查询.md）
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 表: backtest_runs
-- 说明: 回测运行主表，存储每次回测的配置和汇总结果
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS backtest_runs (
    -- 主键
    id VARCHAR(36) PRIMARY KEY,        -- 回测ID（UUID）

    -- 用户信息
    user_id VARCHAR(36),               -- 用户ID（预留，当前版本可为NULL）

    -- 回测配置
    strategy_id VARCHAR(50) NOT NULL,  -- 策略ID
    symbol VARCHAR(20) NOT NULL,       -- 股票代码
    market_id VARCHAR(10),             -- 市场标识（CN_A, HK, US等）
    start_date DATE NOT NULL,          -- 回测开始日期
    end_date DATE NOT NULL,            -- 回测结束日期
    initial_capital NUMERIC(15, 2) NOT NULL,  -- 初始资金

    -- 回测结果（主要指标）
    final_capital NUMERIC(15, 2),      -- 最终资金
    total_return NUMERIC(10, 4),       -- 总收益率（%）
    cagr NUMERIC(10, 4),               -- 年化收益率
    sharpe_ratio NUMERIC(10, 4),       -- Sharpe比率
    sortino_ratio NUMERIC(10, 4),      -- Sortino比率
    calmar_ratio NUMERIC(10, 4),       -- Calmar比率
    max_drawdown NUMERIC(10, 4),       -- 最大回撤（%）

    -- 交易统计
    total_trades INTEGER,              -- 总交易次数
    winning_trades INTEGER,            -- 盈利次数
    losing_trades INTEGER,             -- 亏损次数
    win_rate NUMERIC(10, 4),           -- 胜率（%）
    profit_factor NUMERIC(10, 4),      -- 盈亏比

    -- JSON字段（存储完整配置和指标）
    config JSONB,                      -- 完整配置（策略参数、手续费、滑点等）
    metrics JSONB,                     -- 所有性能指标
    metadata JSONB,                    -- 元数据（引擎版本、数据版本等）

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加表注释
COMMENT ON TABLE backtest_runs IS '回测运行记录主表';
COMMENT ON COLUMN backtest_runs.id IS '回测唯一标识（UUID）';
COMMENT ON COLUMN backtest_runs.config IS '完整回测配置（JSONB格式）';
COMMENT ON COLUMN backtest_runs.metrics IS '所有性能指标（JSONB格式）';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_backtest_runs_user_created
ON backtest_runs(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy
ON backtest_runs(strategy_id);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_symbol
ON backtest_runs(symbol);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_market
ON backtest_runs(market_id);

-- JSONB 字段的 GIN 索引（加速 JSON 查询）
CREATE INDEX IF NOT EXISTS idx_backtest_runs_config_gin
ON backtest_runs USING GIN (config);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_metrics_gin
ON backtest_runs USING GIN (metrics);

-- ----------------------------------------------------------------------------
-- 表: backtest_trades
-- 说明: 回测交易明细表，记录每笔买入/卖出
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS backtest_trades (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 外键
    backtest_id VARCHAR(36) NOT NULL,  -- 关联 backtest_runs.id

    -- 交易信息
    trade_id VARCHAR(50) NOT NULL,     -- 交易ID（内部生成）
    symbol VARCHAR(20) NOT NULL,       -- 股票代码
    side VARCHAR(10) NOT NULL,         -- 买入/卖出 ('buy', 'sell')
    quantity INTEGER NOT NULL,         -- 数量（股）
    price NUMERIC(10, 4) NOT NULL,     -- 成交价格
    amount NUMERIC(15, 2) NOT NULL,    -- 成交金额

    -- 费用
    commission NUMERIC(10, 2),         -- 手续费
    slippage NUMERIC(10, 4),           -- 滑点（bp）
    stamp_tax NUMERIC(10, 2),          -- 印花税

    -- 时间
    executed_at TIMESTAMP NOT NULL,    -- 成交时间

    -- 约束条件
    CONSTRAINT chk_side CHECK (side IN ('buy', 'sell')),
    CONSTRAINT fk_backtest FOREIGN KEY (backtest_id)
        REFERENCES backtest_runs(id) ON DELETE CASCADE
);

-- 添加表注释
COMMENT ON TABLE backtest_trades IS '回测交易明细记录';
COMMENT ON COLUMN backtest_trades.side IS '交易方向：buy(买入) 或 sell(卖出)';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_backtest_trades_backtest
ON backtest_trades(backtest_id);

CREATE INDEX IF NOT EXISTS idx_backtest_trades_symbol
ON backtest_trades(symbol);

CREATE INDEX IF NOT EXISTS idx_backtest_trades_executed_at
ON backtest_trades(executed_at);

-- ----------------------------------------------------------------------------
-- 表: backtest_equity_curve
-- 说明: 权益曲线表，记录每日权益变化
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS backtest_equity_curve (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 外键
    backtest_id VARCHAR(36) NOT NULL,  -- 关联 backtest_runs.id

    -- 权益数据
    date DATE NOT NULL,                -- 日期
    equity NUMERIC(15, 2) NOT NULL,    -- 总权益（现金+持仓）
    capital NUMERIC(15, 2) NOT NULL,   -- 可用现金
    position_value NUMERIC(15, 2),     -- 持仓市值

    -- 约束条件
    CONSTRAINT fk_backtest_equity FOREIGN KEY (backtest_id)
        REFERENCES backtest_runs(id) ON DELETE CASCADE
);

-- 添加表注释
COMMENT ON TABLE backtest_equity_curve IS '回测权益曲线数据';
COMMENT ON COLUMN backtest_equity_curve.equity IS '总权益 = 现金 + 持仓市值';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_backtest_equity_curve_backtest_date
ON backtest_equity_curve(backtest_id, date);

-- ----------------------------------------------------------------------------
-- 示例查询
-- ----------------------------------------------------------------------------

-- 1. 查询用户的历史回测记录
-- SELECT
--     id,
--     strategy_id,
--     symbol,
--     start_date,
--     end_date,
--     total_return,
--     sharpe_ratio,
--     max_drawdown,
--     created_at
-- FROM backtest_runs
-- WHERE user_id = 'user_123'
-- ORDER BY created_at DESC
-- LIMIT 10;

-- 2. 查询某次回测的交易明细
-- SELECT
--     trade_id,
--     symbol,
--     side,
--     quantity,
--     price,
--     amount,
--     commission,
--     executed_at
-- FROM backtest_trades
-- WHERE backtest_id = 'bt_2025111200001'
-- ORDER BY executed_at;

-- 3. 查询权益曲线
-- SELECT
--     date,
--     equity,
--     capital,
--     position_value
-- FROM backtest_equity_curve
-- WHERE backtest_id = 'bt_2025111200001'
-- ORDER BY date;

-- 4. 统计策略表现
-- SELECT
--     strategy_id,
--     COUNT(*) as run_count,
--     AVG(total_return) as avg_return,
--     AVG(sharpe_ratio) as avg_sharpe,
--     AVG(max_drawdown) as avg_drawdown
-- FROM backtest_runs
-- GROUP BY strategy_id
-- ORDER BY avg_sharpe DESC;

-- 5. 查询最佳回测结果
-- SELECT
--     id,
--     strategy_id,
--     symbol,
--     total_return,
--     sharpe_ratio,
--     max_drawdown
-- FROM backtest_runs
-- WHERE total_return > 0
-- ORDER BY sharpe_ratio DESC
-- LIMIT 10;

-- 6. 使用 JSONB 查询特定配置参数
-- SELECT id, strategy_id, config->>'commission_rate' as commission
-- FROM backtest_runs
-- WHERE config->>'commission_rate' = '0.0003';

-- 7. 查询包含特定指标的回测
-- SELECT id, strategy_id, metrics->'risk'->>'max_drawdown' as max_dd
-- FROM backtest_runs
-- WHERE (metrics->'risk'->>'max_drawdown')::numeric < 0.2;

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 数据清理：定期清理旧的回测记录（如6个月前的）
-- 2. 外键级联：删除 backtest_runs 记录会自动删除关联的 trades 和 equity_curve
-- 3. JSONB字段：使用 GIN 索引加速查询，支持复杂的 JSON 查询
-- 4. 索引优化：根据实际查询模式调整索引
-- 5. 分区表：回测记录超过百万条时考虑按月份分区
-- 6. 定期 VACUUM：保持表性能，回收空间
-- ============================================================================
