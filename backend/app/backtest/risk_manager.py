"""
风控管理器模块

负责在回测过程中执行风控规则检查，包括：
- 订单风控：仓位限制
- 持仓风控：止损、止盈、回撤保护
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# 数据结构定义
# ============================================================================


@dataclass
class RiskConfig:
    """风控配置参数"""

    # ============ 仓位控制 ============
    max_position_pct: float = 1.0
    """单票最大仓位比例（相对于总权益）
    - 默认1.0（100%，即不限制）
    - 示例：0.3表示单票最多占30%
    """

    max_total_exposure: float = 1.0
    """最大总仓位比例（所有持仓市值/总权益）
    - 默认1.0（100%，即满仓）
    - 示例：0.95表示最多保留5%现金
    """

    # ============ 止损止盈 ============
    stop_loss_pct: Optional[float] = None
    """止损线（亏损比例）
    - None表示不启用
    - 示例：0.1表示亏损10%时止损
    - 触发条件：current_price < cost_price * (1 - stop_loss_pct)
    """

    stop_profit_pct: Optional[float] = None
    """止盈线（盈利比例）
    - None表示不启用
    - 示例：0.2表示盈利20%时止盈
    - 触发条件：current_price > cost_price * (1 + stop_profit_pct)
    """

    enable_trailing_stop: bool = False
    """是否启用移动止损（暂不实现，预留字段）"""

    # ============ 组合风控 ============
    max_drawdown_pct: Optional[float] = None
    """最大回撤保护阈值
    - None表示不启用
    - 示例：0.2表示从最高点回撤20%时清仓
    - 触发条件：current_equity < peak_equity * (1 - max_drawdown_pct)
    """

    volatility_target: Optional[float] = None
    """目标波动率（年化）- V2功能，暂不实现
    - None表示不启用
    - 示例：0.15表示目标年化波动率15%
    """

    volatility_lookback: int = 20
    """波动率计算回溯期（交易日数）- V2功能"""

    # ============ 其他 ============
    max_leverage: float = 1.0
    """最大杠杆倍数（现货交易固定为1）"""

    def __post_init__(self):
        """参数验证"""
        if not 0 < self.max_position_pct <= 1.0:
            raise ValueError("max_position_pct must be in (0, 1]")
        if not 0 < self.max_total_exposure <= 1.0:
            raise ValueError("max_total_exposure must be in (0, 1]")
        if self.stop_loss_pct is not None and not 0 < self.stop_loss_pct < 1:
            raise ValueError("stop_loss_pct must be in (0, 1)")
        if self.stop_profit_pct is not None and self.stop_profit_pct <= 0:
            raise ValueError("stop_profit_pct must be > 0")
        if self.max_drawdown_pct is not None and not 0 < self.max_drawdown_pct < 1:
            raise ValueError("max_drawdown_pct must be in (0, 1)")


class RiskCheckStatus(str, Enum):
    """风控检查状态"""

    PASSED = "passed"  # 通过
    REJECTED = "rejected"  # 拒绝
    ADJUSTED = "adjusted"  # 调整（暂不实现，预留）


@dataclass
class RiskCheckResult:
    """订单风控检查结果"""

    status: RiskCheckStatus
    """检查状态"""

    reason: Optional[str] = None
    """拒绝原因（status=REJECTED时必填）"""

    original_shares: Optional[int] = None
    """原始订单股数（用于记录）"""

    adjusted_shares: Optional[int] = None
    """调整后股数（status=ADJUSTED时使用，V2功能）"""

    @property
    def passed(self) -> bool:
        """是否通过"""
        return self.status == RiskCheckStatus.PASSED


@dataclass
class ForcedOrder:
    """风控触发的强制订单"""

    symbol: str
    """股票代码"""

    shares: int
    """卖出股数"""

    reason: str
    """触发原因：'stop_loss'/'stop_profit'/'drawdown_protection'"""

    trigger_price: float
    """触发时的价格"""

    cost_price: Optional[float] = None
    """成本价（止损止盈时记录）"""

    pnl_pct: Optional[float] = None
    """盈亏比例（止损止盈时计算）"""


@dataclass
class RiskEvent:
    """风控事件记录（用于metadata）"""

    date: str
    """触发日期（YYYY-MM-DD）"""

    event_type: str
    """事件类型：'order_rejected'/'forced_exit'"""

    symbol: str
    """股票代码"""

    reason: str
    """触发原因"""

    details: Dict[str, Any]
    """详细信息（价格、比例等）"""

    timestamp: str
    """记录时间戳（ISO格式）"""


# ============================================================================
# 风控管理器
# ============================================================================


class RiskManager:
    """风控管理器"""

    def __init__(self, config: RiskConfig, initial_capital: float):
        """
        初始化风控管理器

        Args:
            config: 风控配置
            initial_capital: 初始资金（用于初始化peak_equity）
        """
        self.config = config
        self.peak_equity = initial_capital

    def check_order_risk(self, order: Dict[str, Any], portfolio: Dict[str, Any]) -> RiskCheckResult:
        """
        检查订单是否通过风控

        在TradingEngine执行买入订单前调用

        Args:
            order: 待执行订单，格式：
                {
                    'symbol': str,
                    'shares': int,
                    'price': float
                }
            portfolio: 当前组合状态，格式：
                {
                    'total_equity': float,
                    'cash': float,
                    'positions': {symbol: {'shares': int, 'cost_price': float, ...}},
                    'current_prices': {symbol: float}
                }

        Returns:
            RiskCheckResult: 检查结果（通过/拒绝）
        """
        # 1. 检查单票仓位限制
        result = self._check_position_limit(order, portfolio)
        if not result.passed:
            return result

        # 2. 检查总仓位限制
        result = self._check_exposure_limit(order, portfolio)
        if not result.passed:
            return result

        return RiskCheckResult(status=RiskCheckStatus.PASSED)

    def check_exit_signals(
        self, portfolio: Dict[str, Any], current_data: Dict[str, float]
    ) -> List[ForcedOrder]:
        """
        检查是否触发风控退出信号

        在TradingEngine.process_bar开始时调用

        Args:
            portfolio: 当前组合状态
            current_data: 当前价格数据 {symbol: current_price}

        Returns:
            List[ForcedOrder]: 强制卖出订单列表
        """
        forced_orders = []

        # 1. 检查回撤保护（优先级最高）
        drawdown_orders = self._check_drawdown_protection(portfolio)
        if drawdown_orders:
            return drawdown_orders  # 触发回撤保护时立即返回（清仓）

        # 2. 检查每个持仓的止损止盈
        positions = portfolio.get("positions", {})
        for symbol, position in positions.items():
            current_price = current_data.get(symbol)
            if current_price is None:
                continue

            # 止损检查
            stop_loss_order = self._check_stop_loss(symbol, position, current_price)
            if stop_loss_order:
                forced_orders.append(stop_loss_order)
                continue  # 止损优先，不再检查止盈

            # 止盈检查
            stop_profit_order = self._check_stop_profit(symbol, position, current_price)
            if stop_profit_order:
                forced_orders.append(stop_profit_order)

        return forced_orders

    def update_peak_equity(self, current_equity: float) -> None:
        """
        更新历史最高权益

        Args:
            current_equity: 当前权益
        """
        self.peak_equity = max(self.peak_equity, current_equity)

    # ========== 私有方法 ==========

    def _check_position_limit(
        self, order: Dict[str, Any], portfolio: Dict[str, Any]
    ) -> RiskCheckResult:
        """检查单票仓位限制"""
        symbol = order["symbol"]
        shares = order["shares"]
        price = order["price"]

        # 1. 计算当前持仓市值
        current_position_value = 0
        positions = portfolio.get("positions", {})
        if symbol in positions:
            position = positions[symbol]
            current_position_value = position["shares"] * price

        # 2. 计算订单金额
        order_value = shares * price

        # 3. 计算新仓位占比
        total_equity = portfolio["total_equity"]
        new_position_value = current_position_value + order_value
        new_position_pct = new_position_value / total_equity

        # 4. 判断是否超限
        if new_position_pct > self.config.max_position_pct:
            return RiskCheckResult(
                status=RiskCheckStatus.REJECTED,
                reason=f"单票仓位{new_position_pct:.2%}超过限制{self.config.max_position_pct:.2%}",
                original_shares=shares,
            )

        return RiskCheckResult(status=RiskCheckStatus.PASSED)

    def _check_exposure_limit(
        self, order: Dict[str, Any], portfolio: Dict[str, Any]
    ) -> RiskCheckResult:
        """检查总仓位限制"""
        shares = order["shares"]
        price = order["price"]
        order_value = shares * price

        # 1. 计算当前总持仓市值
        current_total_value = 0
        positions = portfolio.get("positions", {})
        current_prices = portfolio.get("current_prices", {})

        for symbol, position in positions.items():
            current_price = current_prices.get(symbol, position.get("cost_price", 0))
            current_total_value += position["shares"] * current_price

        # 2. 计算新总仓位占比
        total_equity = portfolio["total_equity"]
        new_total_value = current_total_value + order_value
        new_exposure = new_total_value / total_equity

        # 3. 判断是否超限
        if new_exposure > self.config.max_total_exposure:
            return RiskCheckResult(
                status=RiskCheckStatus.REJECTED,
                reason=f"总仓位{new_exposure:.2%}超过限制{self.config.max_total_exposure:.2%}",
                original_shares=shares,
            )

        return RiskCheckResult(status=RiskCheckStatus.PASSED)

    def _check_stop_loss(
        self, symbol: str, position: Dict[str, Any], current_price: float
    ) -> Optional[ForcedOrder]:
        """检查止损"""
        # 1. 未配置止损线则跳过
        if self.config.stop_loss_pct is None:
            return None

        # 2. 计算止损价格
        cost_price = position["cost_price"]
        stop_loss_price = cost_price * (1 - self.config.stop_loss_pct)

        # 3. 判断是否触发
        if current_price <= stop_loss_price:
            pnl_pct = (current_price - cost_price) / cost_price

            return ForcedOrder(
                symbol=symbol,
                shares=position["shares"],
                reason="stop_loss",
                trigger_price=current_price,
                cost_price=cost_price,
                pnl_pct=pnl_pct,
            )

        return None

    def _check_stop_profit(
        self, symbol: str, position: Dict[str, Any], current_price: float
    ) -> Optional[ForcedOrder]:
        """检查止盈"""
        # 1. 未配置止盈线则跳过
        if self.config.stop_profit_pct is None:
            return None

        # 2. 计算止盈价格
        cost_price = position["cost_price"]
        stop_profit_price = cost_price * (1 + self.config.stop_profit_pct)

        # 3. 判断是否触发
        if current_price >= stop_profit_price:
            pnl_pct = (current_price - cost_price) / cost_price

            return ForcedOrder(
                symbol=symbol,
                shares=position["shares"],
                reason="stop_profit",
                trigger_price=current_price,
                cost_price=cost_price,
                pnl_pct=pnl_pct,
            )

        return None

    def _check_drawdown_protection(self, portfolio: Dict[str, Any]) -> List[ForcedOrder]:
        """检查回撤保护"""
        # 1. 未配置回撤保护则跳过
        if self.config.max_drawdown_pct is None:
            return []

        # 2. 更新历史最高权益
        current_equity = portfolio["total_equity"]
        self.peak_equity = max(self.peak_equity, current_equity)

        # 3. 计算当前回撤
        drawdown = (self.peak_equity - current_equity) / self.peak_equity

        # 4. 判断是否触发
        if drawdown >= self.config.max_drawdown_pct:
            # 清空所有持仓
            forced_orders = []
            positions = portfolio.get("positions", {})
            current_prices = portfolio.get("current_prices", {})

            for symbol, position in positions.items():
                current_price = current_prices.get(symbol, position.get("cost_price", 0))
                forced_orders.append(
                    ForcedOrder(
                        symbol=symbol,
                        shares=position["shares"],
                        reason="drawdown_protection",
                        trigger_price=current_price,
                        pnl_pct=-drawdown,  # 记录实际回撤
                    )
                )
            return forced_orders

        return []
