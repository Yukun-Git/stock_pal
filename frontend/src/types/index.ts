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
}

export interface BacktestRequest {
  symbol: string;
  strategy_id: string;
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  commission_rate?: number;
  strategy_params?: Record<string, any>;
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
}
