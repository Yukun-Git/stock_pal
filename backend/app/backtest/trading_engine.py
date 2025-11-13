"""
交易引擎

管理交易状态机，根据信号生成订单，跟踪持仓和资金。

核心功能：
1. 状态机管理：空仓 → 持仓 → 空仓
2. 订单生成：根据交易信号生成买入/卖出订单
3. 持仓管理：跟踪持仓数量、成本、盈亏
4. 资金管理：跟踪可用资金、总权益
"""

from datetime import datetime
from typing import Optional, Dict, List
import logging
import uuid

from .models import (
    Signal, Order, OrderSide, OrderStatus, Trade,
    Position, Portfolio, MarketData, TradingEnvironment
)
from .matching_engine import MatchingEngine
from .rules.validator import TradingRulesValidator

logger = logging.getLogger(__name__)


class TradingEngine:
    """
    交易引擎

    负责整个交易流程的协调：
    1. 接收交易信号
    2. 生成订单
    3. 验证订单（调用 RulesValidator）
    4. 撮合订单（调用 MatchingEngine）
    5. 更新持仓和资金
    """

    def __init__(
        self,
        environment: TradingEnvironment,
        initial_capital: float,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        slippage_bps: float = 5.0,
        stamp_tax_rate: float = 0.001
    ):
        """
        初始化交易引擎

        Args:
            environment: 交易环境
            initial_capital: 初始资金
            commission_rate: 手续费率
            min_commission: 最低手续费
            slippage_bps: 滑点（基点）
            stamp_tax_rate: 印花税率
        """
        self.environment = environment
        self.initial_capital = initial_capital

        # 投资组合
        self.portfolio = Portfolio(
            cash=initial_capital,
            initial_capital=initial_capital
        )

        # 交易记录
        self.orders: List[Order] = []
        self.trades: List[Trade] = []

        # 权益曲线（日期 -> 权益）
        self.equity_history: Dict[datetime, float] = {}

        # 规则验证器
        self.validator = TradingRulesValidator(environment)

        # 撮合引擎
        self.matching_engine = MatchingEngine(
            environment=environment,
            slippage_bps=slippage_bps,
            commission_rate=commission_rate,
            min_commission=min_commission,
            stamp_tax_rate=stamp_tax_rate
        )

        logger.info(
            f"TradingEngine initialized: capital={initial_capital}, "
            f"env={environment}"
        )

    def process_signal(
        self,
        signal: Signal,
        market_data: MarketData,
        current_date: datetime
    ) -> Optional[Trade]:
        """
        处理交易信号

        完整流程：
        1. 解析信号
        2. 生成订单
        3. 验证订单
        4. 撮合订单
        5. 更新持仓
        6. 记录权益

        Args:
            signal: 交易信号
            market_data: 市场数据
            current_date: 当前日期

        Returns:
            Trade: 成交记录（如果成交），否则返回 None
        """
        # 更新持仓的当前价格
        self._update_position_prices(market_data)

        # 记录当日权益
        self.equity_history[current_date] = self.portfolio.total_equity

        # 解析信号
        if signal.action == 0:
            # 持有信号，不操作
            return None
        elif signal.action == 1:
            # 买入信号
            return self._process_buy_signal(signal, market_data, current_date)
        elif signal.action == -1:
            # 卖出信号
            return self._process_sell_signal(signal, market_data, current_date)
        else:
            logger.warning(f"Unknown signal action: {signal.action}")
            return None

    def _process_buy_signal(
        self,
        signal: Signal,
        market_data: MarketData,
        current_date: datetime
    ) -> Optional[Trade]:
        """
        处理买入信号

        Args:
            signal: 买入信号
            market_data: 市场数据
            current_date: 当前日期

        Returns:
            Trade: 成交记录（如果成交）
        """
        # 如果已经持有该股票，不重复买入（简化处理）
        if self.portfolio.has_position(signal.symbol):
            logger.debug(f"Already holding {signal.symbol}, skip buy signal")
            return None

        # 计算可买数量（使用全部可用资金）
        available_cash = self.portfolio.cash
        # 预估手续费（粗略估算）
        estimated_commission = max(
            available_cash * self.matching_engine.commission_rate,
            self.matching_engine.min_commission
        )
        # 可用于买入的资金
        usable_cash = available_cash - estimated_commission * 2  # 保留一些余量

        if usable_cash <= 0:
            logger.debug("Insufficient cash for buying")
            return None

        # 计算数量（向下取整到100的倍数，A股一手=100股）
        quantity = int(usable_cash / signal.price / 100) * 100

        if quantity <= 0:
            logger.debug(f"Cannot afford to buy {signal.symbol}")
            return None

        # 生成买入订单
        order = Order(
            order_id=self._generate_order_id(),
            symbol=signal.symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            limit_price=signal.price,
            created_at=current_date,
            status=OrderStatus.PENDING
        )

        # 执行订单
        return self._execute_order(order, market_data, current_date)

    def _process_sell_signal(
        self,
        signal: Signal,
        market_data: MarketData,
        current_date: datetime
    ) -> Optional[Trade]:
        """
        处理卖出信号

        Args:
            signal: 卖出信号
            market_data: 市场数据
            current_date: 当前日期

        Returns:
            Trade: 成交记录（如果成交）
        """
        # 检查是否持有该股票
        position = self.portfolio.get_position(signal.symbol)
        if not position:
            logger.debug(f"No position in {signal.symbol}, skip sell signal")
            return None

        # 生成卖出订单（全部卖出）
        order = Order(
            order_id=self._generate_order_id(),
            symbol=signal.symbol,
            side=OrderSide.SELL,
            quantity=position.quantity,
            limit_price=signal.price,
            created_at=current_date,
            status=OrderStatus.PENDING
        )

        # 执行订单
        return self._execute_order(order, market_data, current_date)

    def _execute_order(
        self,
        order: Order,
        market_data: MarketData,
        current_date: datetime
    ) -> Optional[Trade]:
        """
        执行订单

        流程：
        1. 验证订单（规则检查）
        2. 撮合订单（生成成交）
        3. 更新持仓和资金

        Args:
            order: 订单
            market_data: 市场数据
            current_date: 当前日期

        Returns:
            Trade: 成交记录（如果成交）
        """
        # 1. 验证订单
        validation_result = self.validator.validate_order(
            order=order,
            market_data=market_data,
            portfolio=self.portfolio,
            current_date=current_date
        )

        if not validation_result.is_valid:
            logger.info(
                f"Order {order.order_id} rejected: {validation_result.error_message}"
            )
            order.status = OrderStatus.REJECTED
            self.orders.append(order)
            return None

        # 2. 撮合订单
        trade = self.matching_engine.match_order(order, market_data)

        if trade is None:
            logger.info(f"Order {order.order_id} cannot be matched")
            order.status = OrderStatus.REJECTED
            self.orders.append(order)
            return None

        # 3. 更新订单状态
        order.status = OrderStatus.FILLED
        self.orders.append(order)
        self.trades.append(trade)

        # 4. 更新持仓和资金
        self._update_portfolio(trade, market_data, current_date)

        logger.info(
            f"Order {order.order_id} executed: {trade.side.value} "
            f"{trade.quantity} shares of {trade.symbol} @ {trade.price:.2f}"
        )

        return trade

    def _update_portfolio(
        self,
        trade: Trade,
        market_data: MarketData,
        current_date: datetime
    ):
        """
        更新投资组合（持仓和资金）

        Args:
            trade: 成交记录
            market_data: 市场数据
            current_date: 当前日期
        """
        if trade.side == OrderSide.BUY:
            # 买入：减少现金，增加持仓
            total_cost = trade.total_cost
            self.portfolio.cash -= total_cost

            # 创建或更新持仓
            self.portfolio.positions[trade.symbol] = Position(
                symbol=trade.symbol,
                quantity=trade.quantity,
                avg_cost=trade.price,
                current_price=market_data.close,
                buy_date=current_date
            )

            logger.debug(
                f"Updated portfolio after buy: cash={self.portfolio.cash:.2f}, "
                f"position={trade.quantity} shares @ {trade.price:.2f}"
            )

        elif trade.side == OrderSide.SELL:
            # 卖出：增加现金，减少持仓
            total_proceeds = trade.amount - trade.commission - trade.stamp_tax
            self.portfolio.cash += total_proceeds

            # 移除持仓
            if trade.symbol in self.portfolio.positions:
                del self.portfolio.positions[trade.symbol]

            logger.debug(
                f"Updated portfolio after sell: cash={self.portfolio.cash:.2f}, "
                f"proceeds={total_proceeds:.2f}"
            )

    def _update_position_prices(self, market_data: MarketData):
        """
        更新持仓的当前价格

        Args:
            market_data: 市场数据
        """
        if market_data.symbol in self.portfolio.positions:
            position = self.portfolio.positions[market_data.symbol]
            # 创建新的 Position 对象（因为是 dataclass）
            self.portfolio.positions[market_data.symbol] = Position(
                symbol=position.symbol,
                quantity=position.quantity,
                avg_cost=position.avg_cost,
                current_price=market_data.close,
                buy_date=position.buy_date
            )

    def _generate_order_id(self) -> str:
        """
        生成订单ID

        Returns:
            str: 订单ID
        """
        return f"ORDER_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def get_current_equity(self) -> float:
        """
        获取当前总权益

        Returns:
            float: 总权益
        """
        return self.portfolio.total_equity

    def get_equity_curve(self) -> Dict[datetime, float]:
        """
        获取权益曲线

        Returns:
            Dict[datetime, float]: 日期 -> 权益
        """
        return self.equity_history

    def get_total_return(self) -> float:
        """
        获取总收益率

        Returns:
            float: 总收益率（百分比）
        """
        if self.initial_capital == 0:
            return 0.0
        return (self.portfolio.total_equity - self.initial_capital) / self.initial_capital

    def get_statistics(self) -> Dict[str, any]:
        """
        获取交易统计

        Returns:
            Dict: 统计信息
        """
        buy_trades = [t for t in self.trades if t.side == OrderSide.BUY]
        sell_trades = [t for t in self.trades if t.side == OrderSide.SELL]

        return {
            'total_orders': len(self.orders),
            'filled_orders': len([o for o in self.orders if o.status == OrderStatus.FILLED]),
            'rejected_orders': len([o for o in self.orders if o.status == OrderStatus.REJECTED]),
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'current_positions': len(self.portfolio.positions),
            'current_cash': self.portfolio.cash,
            'current_equity': self.portfolio.total_equity,
            'total_return_pct': self.get_total_return() * 100,
        }

    def __repr__(self) -> str:
        return (
            f"TradingEngine(env={self.environment}, "
            f"capital={self.initial_capital}, "
            f"equity={self.portfolio.total_equity:.2f}, "
            f"trades={len(self.trades)})"
        )
