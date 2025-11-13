"""
撮合引擎

模拟交易所的撮合逻辑，将订单转换为成交记录。
包含滑点计算、价格验证、涨跌停检查等功能。
"""

from datetime import datetime
from typing import Optional
import logging
import uuid

from .models import (
    Order, OrderSide, Trade, MarketData, StockInfo,
    TradingEnvironment, PriceLimits, Commission
)
from .rules.validator import TradingRulesValidator

logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    撮合引擎

    功能：
    1. 将订单撮合成交易（模拟交易所）
    2. 计算滑点
    3. 验证涨跌停限制
    4. 计算手续费
    5. 生成成交记录
    """

    def __init__(
        self,
        environment: TradingEnvironment,
        slippage_bps: float = 5.0,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        stamp_tax_rate: float = 0.001
    ):
        """
        初始化撮合引擎

        Args:
            environment: 交易环境
            slippage_bps: 滑点（基点，1bp=0.01%），默认5bp
            commission_rate: 手续费率，默认0.03%
            min_commission: 最低手续费，默认5元
            stamp_tax_rate: 印花税率（仅卖出），默认0.1%
        """
        self.environment = environment
        self.slippage_bps = slippage_bps
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.stamp_tax_rate = stamp_tax_rate

        # 规则验证器（用于获取涨跌停价格）
        self.validator = TradingRulesValidator(environment)

    def match_order(
        self,
        order: Order,
        market_data: MarketData,
        stock_info: Optional[StockInfo] = None
    ) -> Optional[Trade]:
        """
        撮合订单

        Args:
            order: 订单
            market_data: 市场数据
            stock_info: 股票信息

        Returns:
            Trade: 成交记录，如果无法成交则返回 None
        """
        # 1. 检查停牌
        if market_data.is_suspended:
            logger.debug(f"Order {order.order_id} rejected: {order.symbol} is suspended")
            return None

        # 2. 检查涨跌停（买入检查涨停，卖出检查跌停）
        if not self._can_execute_at_price_limit(order, market_data, stock_info):
            return None

        # 3. 计算成交价格（基础价格 + 滑点）
        execution_price = self._calculate_execution_price(order, market_data, stock_info)

        # 4. 计算成交金额
        amount = order.quantity * execution_price

        # 5. 计算手续费
        commission_detail = self._calculate_commission(order, amount)

        # 6. 计算滑点金额
        slippage_amount = abs(execution_price - market_data.close) * order.quantity

        # 7. 生成成交记录
        trade = Trade(
            trade_id=self._generate_trade_id(),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            amount=amount,
            commission=commission_detail.total,
            stamp_tax=commission_detail.stamp_tax,
            slippage=slippage_amount,
            executed_at=market_data.date
        )

        logger.info(
            f"Matched order {order.order_id}: {order.side.value} {order.quantity} "
            f"shares of {order.symbol} @ {execution_price:.2f}, "
            f"commission={commission_detail.total:.2f}"
        )

        return trade

    def _can_execute_at_price_limit(
        self,
        order: Order,
        market_data: MarketData,
        stock_info: Optional[StockInfo] = None
    ) -> bool:
        """
        检查是否能在涨跌停板成交

        规则：
        - 买入：涨停无法买入（封板）
        - 卖出：跌停无法卖出（封板）

        Args:
            order: 订单
            market_data: 市场数据
            stock_info: 股票信息

        Returns:
            bool: True=可以成交，False=无法成交
        """
        # 获取涨跌停价格
        price_limits = self.validator.get_price_limits(
            prev_close=market_data.prev_close,
            board=market_data.board_type,
            stock_info=stock_info,
            current_date=market_data.date
        )

        # 如果没有涨跌停限制，直接通过
        if not price_limits.has_limit:
            return True

        # 买入：涨停无法成交
        if order.side == OrderSide.BUY and market_data.is_limit_up:
            logger.debug(
                f"Order {order.order_id} cannot execute: {order.symbol} hit upper limit"
            )
            return False

        # 卖出：跌停无法成交
        if order.side == OrderSide.SELL and market_data.is_limit_down:
            logger.debug(
                f"Order {order.order_id} cannot execute: {order.symbol} hit lower limit"
            )
            return False

        return True

    def _calculate_execution_price(
        self,
        order: Order,
        market_data: MarketData,
        stock_info: Optional[StockInfo] = None
    ) -> float:
        """
        计算成交价格

        成交价格 = 收盘价 ± 滑点
        - 买入：向上滑点（价格更高）
        - 卖出：向下滑点（价格更低）

        同时考虑涨跌停限制。

        Args:
            order: 订单
            market_data: 市场数据
            stock_info: 股票信息

        Returns:
            float: 成交价格
        """
        base_price = market_data.close

        # 计算滑点
        slippage_multiplier = self.slippage_bps / 10000  # bp 转百分比

        if order.side == OrderSide.BUY:
            # 买入：向上滑点
            execution_price = base_price * (1 + slippage_multiplier)
        else:
            # 卖出：向下滑点
            execution_price = base_price * (1 - slippage_multiplier)

        # 获取涨跌停价格
        price_limits = self.validator.get_price_limits(
            prev_close=market_data.prev_close,
            board=market_data.board_type,
            stock_info=stock_info,
            current_date=market_data.date
        )

        # 如果有涨跌停限制，确保价格不超过限制
        if price_limits.has_limit:
            if order.side == OrderSide.BUY and price_limits.upper_limit:
                # 买入价格不能超过涨停价
                execution_price = min(execution_price, price_limits.upper_limit)
            elif order.side == OrderSide.SELL and price_limits.lower_limit:
                # 卖出价格不能低于跌停价
                execution_price = max(execution_price, price_limits.lower_limit)

        # 四舍五入到分
        return round(execution_price, 2)

    def _calculate_commission(
        self,
        order: Order,
        amount: float
    ) -> Commission:
        """
        计算手续费明细

        中国A股手续费结构：
        1. 券商佣金：双向收取，有最低限额
        2. 印花税：仅卖出收取（0.1%）
        3. 过户费：上海股票收取（0.002%）

        Args:
            order: 订单
            amount: 成交金额

        Returns:
            Commission: 手续费明细
        """
        commission = Commission()

        # 1. 券商佣金
        broker_fee = amount * self.commission_rate
        # 最低佣金
        if broker_fee < self.min_commission:
            broker_fee = self.min_commission
        commission.broker_fee = broker_fee

        # 2. 印花税（仅卖出）
        if order.side == OrderSide.SELL:
            commission.stamp_tax = amount * self.stamp_tax_rate

        # 3. 过户费（仅上海股票，6开头）
        if self.environment.market == 'CN' and order.symbol.startswith('6'):
            commission.transfer_fee = amount * 0.00002  # 0.002%

        # 4. 港股通额外费用
        if self.environment.channel == 'CONNECT' and self.environment.market == 'HK':
            # 货币兑换费
            commission.currency_fee = amount * 0.0001  # 0.01%
            # 额外结算费
            commission.settlement_fee = amount * 0.00002

        return commission

    def _generate_trade_id(self) -> str:
        """
        生成成交记录ID

        Returns:
            str: 成交记录ID
        """
        return f"TRADE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def set_slippage(self, slippage_bps: float):
        """
        设置滑点

        Args:
            slippage_bps: 滑点（基点）
        """
        self.slippage_bps = slippage_bps
        logger.info(f"Slippage set to {slippage_bps} bps")

    def set_commission_rate(self, commission_rate: float, min_commission: float):
        """
        设置手续费率

        Args:
            commission_rate: 手续费率
            min_commission: 最低手续费
        """
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        logger.info(
            f"Commission rate set to {commission_rate:.4%}, "
            f"min commission {min_commission}"
        )

    def __repr__(self) -> str:
        return (
            f"MatchingEngine(env={self.environment}, "
            f"slippage={self.slippage_bps}bp, "
            f"commission={self.commission_rate:.4%})"
        )
