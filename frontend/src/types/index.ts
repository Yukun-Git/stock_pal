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
  type: 'buy' | 'sell';
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
}
