-- ============================================================================
-- 回测结果存储模块
-- ============================================================================
-- 功能: 存储回测运行记录、交易明细、权益曲线等结果数据
-- 使用: BacktestService V2 (未来实现)
-- 创建时间: 2025-11-12
-- 状态: 设计中（根据 doc/design/backtest_engine_upgrade_design.md）
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
    initial_capital DECIMAL(15, 2) NOT NULL,  -- 初始资金

    -- 回测结果（主要指标）
    final_capital DECIMAL(15, 2),      -- 最终资金
    total_return DECIMAL(10, 4),       -- 总收益率（%）
    cagr DECIMAL(10, 4),               -- 年化收益率
    sharpe_ratio DECIMAL(10, 4),       -- Sharpe比率
    sortino_ratio DECIMAL(10, 4),      -- Sortino比率
    calmar_ratio DECIMAL(10, 4),       -- Calmar比率
    max_drawdown DECIMAL(10, 4),       -- 最大回撤（%）

    -- 交易统计
    total_trades INTEGER,              -- 总交易次数
    winning_trades INTEGER,            -- 盈利次数
    losing_trades INTEGER,             -- 亏损次数
    win_rate DECIMAL(10, 4),           -- 胜率（%）
    profit_factor DECIMAL(10, 4),      -- 盈亏比

    -- JSON字段（存储完整配置和指标）
    config JSON,                       -- 完整配置（策略参数、手续费、滑点等）
    metrics JSON,                      -- 所有性能指标
    metadata JSON,                     -- 元数据（引擎版本、数据版本等）

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_user_created (user_id, created_at),
    INDEX idx_strategy (strategy_id),
    INDEX idx_symbol (symbol),
    INDEX idx_market (market_id)
);

-- ----------------------------------------------------------------------------
-- 表: backtest_trades
-- 说明: 回测交易明细表，记录每笔买入/卖出
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS backtest_trades (
    -- 主键
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 外键
    backtest_id VARCHAR(36) NOT NULL,  -- 关联 backtest_runs.id

    -- 交易信息
    trade_id VARCHAR(50) NOT NULL,     -- 交易ID（内部生成）
    symbol VARCHAR(20) NOT NULL,       -- 股票代码
    side ENUM('buy', 'sell') NOT NULL, -- 买入/卖出
    quantity INT NOT NULL,             -- 数量（股）
    price DECIMAL(10, 4) NOT NULL,     -- 成交价格
    amount DECIMAL(15, 2) NOT NULL,    -- 成交金额

    -- 费用
    commission DECIMAL(10, 2),         -- 手续费
    slippage DECIMAL(10, 4),           -- 滑点（bp）
    stamp_tax DECIMAL(10, 2),          -- 印花税

    -- 时间
    executed_at DATETIME NOT NULL,     -- 成交时间

    -- 外键约束
    FOREIGN KEY (backtest_id) REFERENCES backtest_runs(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_backtest (backtest_id),
    INDEX idx_symbol (symbol),
    INDEX idx_executed_at (executed_at)
);

-- ----------------------------------------------------------------------------
-- 表: backtest_equity_curve
-- 说明: 权益曲线表，记录每日权益变化
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS backtest_equity_curve (
    -- 主键
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 外键
    backtest_id VARCHAR(36) NOT NULL,  -- 关联 backtest_runs.id

    -- 权益数据
    date DATE NOT NULL,                -- 日期
    equity DECIMAL(15, 2) NOT NULL,    -- 总权益（现金+持仓）
    capital DECIMAL(15, 2) NOT NULL,   -- 可用现金
    position_value DECIMAL(15, 2),     -- 持仓市值

    -- 外键约束
    FOREIGN KEY (backtest_id) REFERENCES backtest_runs(id) ON DELETE CASCADE,

    -- 索引
    INDEX idx_backtest_date (backtest_id, date)
);

-- ----------------------------------------------------------------------------
-- SQLite 版本（当前使用）
-- ----------------------------------------------------------------------------
-- 注意：上面使用的是MySQL语法，SQLite需要调整：
-- 1. AUTO_INCREMENT 改为 AUTOINCREMENT
-- 2. ENUM 改为 TEXT + CHECK 约束
-- 3. JSON 字段在SQLite中存储为TEXT
-- 4. 外键需要 PRAGMA foreign_keys = ON;
-- 5. 索引定义分开创建

-- SQLite 适配版本：

-- PRAGMA foreign_keys = ON;

-- CREATE TABLE IF NOT EXISTS backtest_runs (
--     id TEXT PRIMARY KEY,
--     user_id TEXT,
--     strategy_id TEXT NOT NULL,
--     symbol TEXT NOT NULL,
--     market_id TEXT,
--     start_date DATE NOT NULL,
--     end_date DATE NOT NULL,
--     initial_capital REAL NOT NULL,
--     final_capital REAL,
--     total_return REAL,
--     cagr REAL,
--     sharpe_ratio REAL,
--     sortino_ratio REAL,
--     calmar_ratio REAL,
--     max_drawdown REAL,
--     total_trades INTEGER,
--     winning_trades INTEGER,
--     losing_trades INTEGER,
--     win_rate REAL,
--     profit_factor REAL,
--     config TEXT,      -- JSON as TEXT
--     metrics TEXT,     -- JSON as TEXT
--     metadata TEXT,    -- JSON as TEXT
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE INDEX IF NOT EXISTS idx_user_created ON backtest_runs(user_id, created_at);
-- CREATE INDEX IF NOT EXISTS idx_strategy ON backtest_runs(strategy_id);
-- CREATE INDEX IF NOT EXISTS idx_symbol ON backtest_runs(symbol);
-- CREATE INDEX IF NOT EXISTS idx_market ON backtest_runs(market_id);

-- CREATE TABLE IF NOT EXISTS backtest_trades (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     backtest_id TEXT NOT NULL,
--     trade_id TEXT NOT NULL,
--     symbol TEXT NOT NULL,
--     side TEXT NOT NULL CHECK(side IN ('buy', 'sell')),
--     quantity INTEGER NOT NULL,
--     price REAL NOT NULL,
--     amount REAL NOT NULL,
--     commission REAL,
--     slippage REAL,
--     stamp_tax REAL,
--     executed_at DATETIME NOT NULL,
--     FOREIGN KEY (backtest_id) REFERENCES backtest_runs(id) ON DELETE CASCADE
-- );

-- CREATE INDEX IF NOT EXISTS idx_backtest_trades ON backtest_trades(backtest_id);
-- CREATE INDEX IF NOT EXISTS idx_trade_symbol ON backtest_trades(symbol);

-- CREATE TABLE IF NOT EXISTS backtest_equity_curve (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     backtest_id TEXT NOT NULL,
--     date DATE NOT NULL,
--     equity REAL NOT NULL,
--     capital REAL NOT NULL,
--     position_value REAL,
--     FOREIGN KEY (backtest_id) REFERENCES backtest_runs(id) ON DELETE CASCADE
-- );

-- CREATE INDEX IF NOT EXISTS idx_equity_backtest_date ON backtest_equity_curve(backtest_id, date);

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

-- ============================================================================
-- 维护说明
-- ============================================================================
-- 1. 数据清理：定期清理旧的回测记录（如6个月前的）
-- 2. 外键级联：删除 backtest_runs 记录会自动删除关联的 trades 和 equity_curve
-- 3. JSON字段：使用时需解析，考虑性能影响
-- 4. 索引优化：根据实际查询模式调整索引
-- ============================================================================
