export interface Stock {
  code: string;
  name: string;
  market?: string;
}

export interface StrategyParameter {
  name: string;
  label: string;
  type: 'integer' | 'float' | 'string' | 'boolean' | 'select';
  default: any;
  min?: number;
  max?: number;
  description?: string;
  options?: Array<{ value: string; label: string }>;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  parameters: StrategyParameter[];
}

export interface StrategyDocumentation {
  strategy_id: string;
  strategy_name: string;
  content: string;
}

export interface KLine {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  signal?: number;
}

export interface Trade {
  date: string;
  action: 'buy' | 'sell';  // 修复：字段名应为 action（与后端一致）
  price: number;
  shares: number;
  amount: number;
  commission: number;
  capital: number;
  profit?: number;
  profit_pct?: number;
  reason?: string;  // 新增：退出原因（strategy_signal, stop_loss, stop_profit, drawdown_protection）
}

export interface EquityPoint {
  date: string;
  equity: number;
  capital: number;
  position_value: number;
}

export interface BacktestResult {
  // ===== 基础指标（向后兼容）=====
  initial_capital: number;
  final_capital: number;
  total_return: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  max_drawdown: number;
  avg_profit: number;
  avg_loss: number;
  profit_factor: number;

  // ===== 新增增强指标 =====
  // 收益指标
  cagr?: number;                      // 年化收益率

  // 风险指标
  volatility?: number;                // 波动率（年化）
  max_drawdown_duration?: number;     // 最大回撤持续期（天）

  // 风险调整收益
  sharpe_ratio?: number;              // 夏普比率
  sortino_ratio?: number;             // 索提诺比率
  calmar_ratio?: number;              // 卡玛比率

  // 交易统计
  avg_trade_return?: number;          // 平均交易收益率
  avg_holding_period?: number;        // 平均持仓天数
  turnover_rate?: number;             // 换手率（年化）

  // ===== 基准对比指标（新增）=====
  alpha?: number;                     // Alpha（超额收益）
  beta?: number;                      // Beta（系统风险）
  information_ratio?: number;         // 信息比率
  tracking_error?: number;            // 跟踪误差

  // ===== 风控统计 =====
  risk_stats?: RiskStats;             // 风控统计数据
}

export interface BacktestRequest {
  symbol: string;
  strategy_id: string;
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  commission_rate?: number;
  strategy_params?: Record<string, any>;
  benchmark?: string;                // 新增：基准指数ID（可选）
}

export interface BenchmarkOption {
  id: string;
  code: string;
  name: string;
  description: string;
}

export interface StrategyAnalysis {
  strategy_id: string;
  strategy_name: string;
  status: string;
  proximity?: string;
  indicators?: Record<string, any>;
  current_state: string;
  proximity_description: string;
  suggestion: string;
  message?: string;
}

export interface SignalAnalysis {
  date: string;
  close_price: number;
  analyses: StrategyAnalysis[];
  status?: string;
  message?: string;
}

export interface BacktestMetadata {
  backtest_id: string;               // 回测唯一ID
  engine_version: string;            // 引擎版本
  execution_time_seconds: number;    // 执行时间（秒）
  environment?: string;              // 交易环境
  started_at?: string;               // 开始时间
  risk_events?: RiskEvent[];         // 新增：风控事件列表
}

export interface BenchmarkMetrics {
  total_return: number;              // 总收益率
  cagr: number;                      // 年化收益率
  sharpe_ratio: number;              // 夏普比率
  max_drawdown: number;              // 最大回撤
  volatility: number;                // 波动率
}

export interface Benchmark {
  id: string;                        // 基准ID（如CSI300）
  name: string;                      // 基准名称（如沪深300）
  equity_curve?: EquityPoint[];      // 基准权益曲线（可选）
  metrics?: BenchmarkMetrics;        // 基准指标（可选，获取失败时为空）
  error?: boolean;                   // 是否有错误
  message?: string;                  // 错误消息（如果有）
}

export interface BacktestResponse {
  stock: Stock;
  strategy: string | {
    strategies: string[];
    combine_mode: string;
    vote_threshold?: number;
  };
  results: BacktestResult;
  trades: Trade[];
  equity_curve: EquityPoint[];
  klines: KLine[];
  buy_points: Array<{ date: string; price: number }>;
  sell_points: Array<{ date: string; price: number }>;
  signal_analysis?: SignalAnalysis;
  metadata?: BacktestMetadata;       // 新增：元数据
  benchmark?: Benchmark;             // 新增：基准数据
}

// ===== 风控管理相关类型 =====

/**
 * 风控配置
 */
export interface RiskConfig {
  // 止损止盈
  stop_loss_pct?: number | null;         // 止损百分比（如0.1表示-10%）
  stop_profit_pct?: number | null;       // 止盈百分比（如0.2表示+20%）

  // 仓位控制
  max_position_pct: number;              // 单票最大仓位（如0.3表示30%）
  max_total_exposure: number;            // 总仓位上限（如0.95表示95%）

  // 组合风控
  max_drawdown_pct?: number | null;      // 最大回撤保护（如0.2表示20%）
}

/**
 * 风控模板类型
 */
export type RiskTemplate = 'conservative' | 'balanced' | 'aggressive' | 'custom' | null;

/**
 * 风控统计
 */
export interface RiskStats {
  stop_loss_count: number;               // 止损触发次数
  stop_profit_count: number;             // 止盈触发次数
  drawdown_protection_count: number;     // 回撤保护触发次数
  rejected_orders_count: number;         // 拒绝订单次数
  stop_loss_saved_loss?: number;         // 止损避免的额外亏损
  stop_profit_locked_profit?: number;    // 止盈锁定的收益
  drawdown_protection_saved_loss?: number; // 回撤保护避免的亏损
}

/**
 * 风控事件类型
 */
export type RiskEventType = 'stop_loss' | 'stop_profit' | 'drawdown_protection' | 'rejected_order';

/**
 * 风控事件
 */
export interface RiskEvent {
  date: string;                          // 事件日期
  type: RiskEventType;                   // 事件类型
  symbol?: string;                       // 股票代码
  price?: number;                        // 触发价格
  cost_price?: number;                   // 成本价格
  reason: string;                        // 触发原因
  details?: Record<string, any>;         // 额外详情
}

// ===== 自选股管理相关类型 =====

/**
 * 自选股分组
 */
export interface WatchlistGroup {
  id: number;
  user_id: number;
  name: string;
  color?: string;
  sort_order: number;
  is_default?: boolean;
  stock_count?: number;
  created_at: string;
  updated_at: string;
}

/**
 * 自选股股票
 */
export interface WatchlistStock {
  id: number;
  user_id: number;
  stock_code: string;
  stock_name: string;
  group_id?: number | null;
  group_name?: string;
  note?: string;
  created_at: string;
  updated_at: string;
  quote?: WatchlistQuote;  // 实时行情（Phase 3）
}

/**
 * 实时行情数据（Phase 3）
 */
export interface WatchlistQuote {
  code: string;
  name: string;
  price: number;
  change_pct: number;
  change_amount: number;
  volume: number;
  turnover: number;
  turnover_rate: number;
  high: number;
  low: number;
  open: number;
  pre_close: number;
  timestamp: string;
}

/**
 * 添加自选股请求
 */
export interface AddWatchlistStockRequest {
  stock_code: string;
  stock_name: string;
  group_id?: number;
  note?: string;
}

/**
 * 更新自选股请求
 */
export interface UpdateWatchlistStockRequest {
  group_id?: number;
  note?: string;
}

/**
 * 批量删除自选股请求
 */
export interface BatchDeleteWatchlistRequest {
  ids: number[];
}

/**
 * 批量导入自选股请求
 */
export interface BatchImportWatchlistRequest {
  stocks: Array<{
    stock_code: string;
    stock_name: string;
  }>;
  group_id?: number;
  skip_duplicates?: boolean;
}

/**
 * 批量导入自选股响应
 */
export interface BatchImportWatchlistResponse {
  imported_count: number;
  skipped_count: number;
  failed: Array<{
    stock_code?: string;
    stock_name?: string;
    stock?: any;
    reason: string;
  }>;
}

/**
 * 创建分组请求
 */
export interface CreateGroupRequest {
  name: string;
  color?: string;
  sort_order?: number;
}

/**
 * 更新分组请求
 */
export interface UpdateGroupRequest {
  name?: string;
  color?: string;
  sort_order?: number;
}

/**
 * 检查股票是否在自选股响应
 */
export interface CheckWatchlistResponse {
  in_watchlist: boolean;
  watchlist_id?: number;
  group_name?: string;
}

// ===== 数据源适配器相关类型 =====

/**
 * 数据源适配器元数据
 */
export interface DataAdapter {
  name: string;                          // 适配器名称（如 akshare, yfinance）
  display_name: string;                  // 显示名称（如 AkShare (东方财富)）
  supported_markets: string[];           // 支持的市场类型
  requires_auth: boolean;                // 是否需要认证
  timeout: number;                       // 超时时间（秒）
}

/**
 * 适配器健康状态
 */
export type AdapterHealthStatus = 'online' | 'offline' | 'error' | 'unknown';

/**
 * 适配器健康检查结果
 */
export interface AdapterHealth {
  status: AdapterHealthStatus;
  response_time_ms: number;
  message: string;
  checked_at: string;
}

/**
 * 适配器性能指标
 */
export interface AdapterMetrics {
  success_count: number;
  fail_count: number;
  total_response_ms: number;
  last_success: string | null;
  last_failure: string | null;
  last_error?: string;
  avg_response_ms?: number;
}

/**
 * 适配器状态（包含元数据+健康+指标）
 */
export interface AdapterStatus extends DataAdapter {
  health_status: AdapterHealthStatus;
  last_check: string | null;
  metrics: AdapterMetrics;
}

/**
 * 健康检查汇总
 */
export interface HealthSummary {
  total: number;
  online: number;
  offline: number;
  error: number;
}

/**
 * 健康检查响应
 */
export interface HealthCheckResponse {
  summary: HealthSummary;
  adapters: Record<string, AdapterHealth>;
}

