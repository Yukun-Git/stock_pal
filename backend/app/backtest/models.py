"""
数据模型定义

定义回测系统中使用的所有数据结构，包括：
- 交易信号、订单、成交记录
- 持仓、市场数据
- 回测配置和结果
- 交易环境（三层架构）
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd


# ==================== 枚举类型 ====================

class OrderSide(Enum):
    """订单方向"""
    BUY = 'buy'
    SELL = 'sell'


class OrderStatus(Enum):
    """订单状态"""
    PENDING = 'pending'     # 待成交
    FILLED = 'filled'       # 已成交
    REJECTED = 'rejected'   # 已拒绝
    CANCELED = 'canceled'   # 已撤销


class Market(Enum):
    """市场（Layer 1）"""
    CN = 'CN'  # 中国大陆
    HK = 'HK'  # 香港
    US = 'US'  # 美国


class Board(Enum):
    """板块（Layer 2）"""
    # 中国大陆板块
    MAIN = 'MAIN'    # 主板（沪深）
    GEM = 'GEM'      # 创业板
    STAR = 'STAR'    # 科创板
    BSE = 'BSE'      # 北交所
    ST = 'ST'        # ST股票

    # 香港板块
    HK_MAIN = 'HK_MAIN'
    HK_GEM = 'HK_GEM'

    # 美国板块
    US_NYSE = 'US_NYSE'
    US_NASDAQ = 'US_NASDAQ'


class Channel(Enum):
    """交易渠道（Layer 3）"""
    DIRECT = 'DIRECT'      # 直接交易
    CONNECT = 'CONNECT'    # 互联互通（如沪深港通）
    QDII = 'QDII'          # QDII基金通道


# ==================== 交易环境（三层架构核心） ====================

@dataclass(frozen=True)
class TradingEnvironment:
    """
    交易环境：市场+板块+渠道的组合

    三层架构：
    - Layer 1 (Market): 市场基础规则（T+1/T+2、交易时段、基础费用）
    - Layer 2 (Board): 板块特定规则（涨跌停比例、新股规则）
    - Layer 3 (Channel): 渠道规则（额外费用、限制）

    示例:
        CN_MAIN_DIRECT: A股主板直接交易
        HK_MAIN_CONNECT: 港股通
        CN_GEM_DIRECT: 创业板直接交易
    """
    market: str           # CN, HK, US
    board: str            # MAIN, GEM, STAR, BSE, ST
    channel: str = 'DIRECT'  # DIRECT, CONNECT, QDII

    def __str__(self) -> str:
        """生成唯一标识符"""
        if self.channel == 'DIRECT':
            return f"{self.market}_{self.board}"
        else:
            return f"{self.market}_{self.board}_{self.channel}"

    def __repr__(self) -> str:
        return f"TradingEnvironment(market='{self.market}', board='{self.board}', channel='{self.channel}')"


# ==================== 交易数据类 ====================

@dataclass(frozen=True)
class Signal:
    """
    交易信号

    由策略生成，表示买入/卖出/持有的意图
    """
    symbol: str
    date: datetime
    action: int  # 1=买入, -1=卖出, 0=持有
    price: float
    reason: Optional[str] = None


@dataclass
class Order:
    """
    订单

    由交易引擎根据信号生成，待撮合引擎执行
    """
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    limit_price: float
    created_at: datetime
    status: OrderStatus = OrderStatus.PENDING

    def __repr__(self) -> str:
        return (f"Order(id={self.order_id}, {self.side.value} {self.quantity} "
                f"shares of {self.symbol} @ {self.limit_price:.2f})")


@dataclass
class Trade:
    """
    成交记录

    订单执行后的实际成交结果
    """
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float              # 实际成交价（含滑点）
    amount: float             # 成交金额 = quantity * price
    commission: float         # 手续费
    stamp_tax: float = 0.0    # 印花税
    slippage: float = 0.0     # 滑点金额
    executed_at: datetime = None

    def __post_init__(self):
        if self.executed_at is None:
            self.executed_at = datetime.now()

    @property
    def total_cost(self) -> float:
        """总成本（含手续费和印花税）"""
        return self.amount + self.commission + self.stamp_tax

    def __repr__(self) -> str:
        return (f"Trade(id={self.trade_id}, {self.side.value} {self.quantity} "
                f"shares of {self.symbol} @ {self.price:.2f}, "
                f"cost={self.total_cost:.2f})")


@dataclass
class Position:
    """
    持仓

    跟踪当前持有的股票数量、成本、市值等
    """
    symbol: str
    quantity: int
    avg_cost: float           # 平均持仓成本
    current_price: float      # 当前价格
    buy_date: datetime        # 买入日期（用于T+1检查）

    @property
    def market_value(self) -> float:
        """市值"""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """成本"""
        return self.quantity * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        """未实现盈亏"""
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """未实现盈亏率"""
        if self.cost_basis == 0:
            return 0.0
        return self.unrealized_pnl / self.cost_basis

    def __repr__(self) -> str:
        return (f"Position({self.symbol}, {self.quantity} shares, "
                f"cost={self.avg_cost:.2f}, current={self.current_price:.2f}, "
                f"P&L={self.unrealized_pnl:.2f})")


@dataclass
class MarketData:
    """
    市场数据

    单日的OHLCV数据及状态标识
    """
    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    prev_close: float         # 昨收价（用于涨跌停计算）

    # 状态标识
    is_suspended: bool = False      # 是否停牌
    is_limit_up: bool = False       # 是否涨停
    is_limit_down: bool = False     # 是否跌停

    # 板块信息
    board_type: str = 'MAIN'        # 板块类型
    stock_name: Optional[str] = None  # 股票名称（用于ST判断）

    def __repr__(self) -> str:
        return (f"MarketData({self.symbol}, {self.date.date()}, "
                f"close={self.close:.2f}, volume={self.volume:.0f})")


@dataclass
class StockInfo:
    """
    股票信息

    包含股票的基本信息和上市信息
    """
    symbol: str
    name: str
    board: str                      # 板块
    ipo_date: Optional[datetime] = None  # IPO日期（用于新股规则）
    is_st: bool = False            # 是否ST股票

    def __repr__(self) -> str:
        return f"StockInfo({self.symbol}, {self.name}, {self.board})"


# ==================== 投资组合 ====================

@dataclass
class Portfolio:
    """
    投资组合

    跟踪资金、持仓、权益等
    """
    cash: float                              # 可用资金
    positions: Dict[str, Position] = field(default_factory=dict)  # 持仓字典
    initial_capital: float = 0.0             # 初始资金

    def __post_init__(self):
        if self.initial_capital == 0.0:
            self.initial_capital = self.cash

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_equity(self) -> float:
        """总权益 = 现金 + 持仓市值"""
        return self.cash + self.market_value

    @property
    def total_return(self) -> float:
        """总收益"""
        return self.total_equity - self.initial_capital

    @property
    def total_return_pct(self) -> float:
        """总收益率"""
        if self.initial_capital == 0:
            return 0.0
        return self.total_return / self.initial_capital

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """是否持有该股票"""
        return symbol in self.positions and self.positions[symbol].quantity > 0

    def __repr__(self) -> str:
        return (f"Portfolio(cash={self.cash:.2f}, "
                f"market_value={self.market_value:.2f}, "
                f"equity={self.total_equity:.2f}, "
                f"positions={len(self.positions)})")


# ==================== 风控配置 ====================

@dataclass
class RiskConfig:
    """
    风控配置

    定义风险控制规则的参数
    """
    max_position_pct: float = 0.3           # 单票最大仓位 30%
    stop_loss_pct: float = 0.1              # 止损线 10%
    stop_profit_pct: Optional[float] = None # 止盈线（可选）
    max_drawdown_pct: float = 0.2           # 最大回撤 20%
    max_leverage: float = 1.0               # 最大杠杆（现货=1）

    def __repr__(self) -> str:
        return (f"RiskConfig(max_position={self.max_position_pct:.1%}, "
                f"stop_loss={self.stop_loss_pct:.1%})")


# ==================== 回测配置 ====================

@dataclass
class BacktestConfig:
    """
    回测配置

    定义回测的所有输入参数
    """
    # 基础参数
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100000

    # 成本参数
    commission_rate: float = 0.0003      # 手续费率 0.03%
    min_commission: float = 5.0          # 最低手续费
    slippage_bps: float = 5.0            # 滑点 5bp
    stamp_tax_rate: float = 0.001        # 印花税 0.1% (仅卖出)

    # 风控参数
    risk_config: Optional[RiskConfig] = None

    # 基准对比
    benchmark: Optional[str] = 'CSI300'  # 沪深300

    # 策略参数
    strategy_id: Optional[str] = None
    strategy_params: Optional[Dict[str, Any]] = None

    # 交易环境（三层架构）
    trading_environment: Optional[TradingEnvironment] = None

    # 元数据
    data_version: Optional[str] = None
    engine_version: str = '2.0.0'

    def __repr__(self) -> str:
        return (f"BacktestConfig({self.symbol}, {self.start_date} to {self.end_date}, "
                f"capital={self.initial_capital:.0f})")


# ==================== 回测结果 ====================

@dataclass
class BacktestResult:
    """
    回测结果

    包含完整的回测输出
    """
    # 配置信息
    config: BacktestConfig

    # 交易记录
    trades: List[Trade]
    equity_curve: pd.DataFrame  # 包含日期、权益、现金、持仓市值

    # 性能指标
    metrics: Dict[str, float]

    # 基准对比（可选）
    benchmark_metrics: Optional[Dict[str, float]] = None

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        total_return = self.metrics.get('total_return', 0)
        sharpe = self.metrics.get('sharpe_ratio', 0)
        return (f"BacktestResult(trades={len(self.trades)}, "
                f"return={total_return:.2%}, sharpe={sharpe:.2f})")


# ==================== 验证结果 ====================

@dataclass
class ValidationResult:
    """
    规则验证结果

    用于交易规则验证的返回值
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def error_message(self) -> str:
        """错误信息（多行）"""
        return '\n'.join(self.errors)

    def __bool__(self) -> bool:
        return self.is_valid

    def __repr__(self) -> str:
        if self.is_valid:
            return "ValidationResult(valid=True)"
        else:
            return f"ValidationResult(valid=False, errors={len(self.errors)})"


@dataclass
class CheckItem:
    """
    单项检查结果

    用于风控检查的细粒度结果
    """
    passed: bool
    reason: Optional[str] = None

    def __bool__(self) -> bool:
        return self.passed


# ==================== 涨跌停价格 ====================

@dataclass
class PriceLimits:
    """
    涨跌停价格

    板块特定的价格限制
    """
    upper_limit: Optional[float]  # 涨停价（None表示无限制）
    lower_limit: Optional[float]  # 跌停价（None表示无限制）
    has_limit: bool               # 是否有涨跌停限制

    def __repr__(self) -> str:
        if not self.has_limit:
            return "PriceLimits(no limit)"
        return f"PriceLimits(up={self.upper_limit:.2f}, down={self.lower_limit:.2f})"


# ==================== 手续费明细 ====================

@dataclass
class Commission:
    """
    手续费明细

    包含各项费用的详细拆分
    """
    broker_fee: float = 0.0        # 券商佣金
    stamp_tax: float = 0.0         # 印花税
    transfer_fee: float = 0.0      # 过户费
    settlement_fee: float = 0.0    # 结算费（港股）
    currency_fee: float = 0.0      # 货币兑换费（港股通）

    @property
    def total(self) -> float:
        """总费用"""
        return (self.broker_fee + self.stamp_tax + self.transfer_fee +
                self.settlement_fee + self.currency_fee)

    def __repr__(self) -> str:
        return f"Commission(total={self.total:.2f})"


# ==================== 交易上下文 ====================

@dataclass
class TradingContext:
    """
    交易上下文

    包含回测执行过程中的上下文信息
    """
    current_date: datetime
    trading_days: List[datetime] = field(default_factory=list)
    stock_info: Optional[StockInfo] = None

    def __repr__(self) -> str:
        return f"TradingContext(date={self.current_date.date()})"
