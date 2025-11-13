"""
交易规则验证器

实现三层架构的交易规则验证：
- Layer 1 (Market): 市场基础规则（T+1/T+2、交易时段）
- Layer 2 (Board): 板块特定规则（涨跌停比例）
- Layer 3 (Channel): 渠道规则（额外费用）

当前版本：MVP - 重点实现 A股基础规则
"""

from datetime import datetime
from typing import Optional, Dict, Tuple
import logging

from ..models import (
    Order, OrderSide, MarketData, Portfolio, Position,
    TradingEnvironment, ValidationResult, PriceLimits, StockInfo
)
from .trading_calendar import TradingCalendar, get_trading_calendar

logger = logging.getLogger(__name__)


class TradingRulesValidator:
    """
    交易规则验证器

    验证订单是否符合市场交易规则，包括：
    - T+1 制度：当日买入不能当日卖出
    - 涨跌停约束：不同板块有不同的涨跌停限制
    - 停牌检查：停牌期间不能交易
    - 交易时段：只能在交易时段内交易
    """

    def __init__(self, environment: TradingEnvironment):
        """
        初始化规则验证器

        Args:
            environment: 交易环境（市场+板块+渠道）
        """
        self.environment = environment
        self.calendar = get_trading_calendar(environment.market)

        # 加载板块规则配置
        self.price_limit_rules = self._load_price_limit_rules()

    def _load_price_limit_rules(self) -> Dict[str, Tuple[float, float]]:
        """
        加载涨跌停规则配置

        Returns:
            Dict[board, (up_limit_pct, down_limit_pct)]
        """
        # 中国A股涨跌停规则
        if self.environment.market == 'CN':
            return {
                'MAIN': (0.10, 0.10),   # 主板 ±10%
                'GEM': (0.20, 0.20),     # 创业板 ±20%
                'STAR': (0.20, 0.20),    # 科创板 ±20%
                'BSE': (0.30, 0.30),     # 北交所 ±30%
                'ST': (0.05, 0.05),      # ST股票 ±5%
            }
        # 港股无涨跌停
        elif self.environment.market == 'HK':
            return {
                'MAIN': (None, None),
                'HK_MAIN': (None, None),
            }
        # 美股无涨跌停
        elif self.environment.market == 'US':
            return {
                'NYSE': (None, None),
                'NASDAQ': (None, None),
            }
        else:
            logger.warning(f"Unknown market: {self.environment.market}")
            return {}

    def validate_order(
        self,
        order: Order,
        market_data: MarketData,
        portfolio: Portfolio,
        current_date: datetime,
        stock_info: Optional[StockInfo] = None
    ) -> ValidationResult:
        """
        验证订单是否符合交易规则

        Args:
            order: 订单
            market_data: 市场数据
            portfolio: 投资组合
            current_date: 当前日期
            stock_info: 股票信息（用于IPO判断等）

        Returns:
            ValidationResult: 验证结果
        """
        errors = []

        # 1. 检查停牌
        if not self._validate_not_suspended(order, market_data):
            errors.append(f"{order.symbol} 停牌，无法交易")

        # 2. 检查交易日
        if not self._validate_trading_day(current_date):
            errors.append(f"{current_date.date()} 不是交易日")

        # 3. 检查 T+1 约束（仅卖出时）
        if order.side == OrderSide.SELL:
            t1_result = self._validate_t_plus_1(order, portfolio, current_date)
            if not t1_result.is_valid:
                errors.extend(t1_result.errors)

        # 4. 检查涨跌停（买入时检查涨停，卖出时检查跌停）
        price_limit_result = self._validate_price_limit(order, market_data, stock_info)
        if not price_limit_result.is_valid:
            errors.extend(price_limit_result.errors)

        # 5. 检查资金/持仓充足（买入检查资金，卖出检查持仓）
        balance_result = self._validate_balance(order, portfolio)
        if not balance_result.is_valid:
            errors.extend(balance_result.errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def _validate_not_suspended(self, order: Order, market_data: MarketData) -> bool:
        """
        检查是否停牌

        Args:
            order: 订单
            market_data: 市场数据

        Returns:
            bool: True=未停牌，False=已停牌
        """
        if market_data.is_suspended:
            logger.debug(f"{order.symbol} is suspended on {market_data.date.date()}")
            return False
        return True

    def _validate_trading_day(self, date: datetime) -> bool:
        """
        检查是否为交易日

        Args:
            date: 日期

        Returns:
            bool: True=交易日，False=非交易日
        """
        is_trading_day = self.calendar.is_trading_day(date)
        if not is_trading_day:
            logger.debug(f"{date.date()} is not a trading day")
        return is_trading_day

    def _validate_t_plus_1(
        self,
        order: Order,
        portfolio: Portfolio,
        current_date: datetime
    ) -> ValidationResult:
        """
        验证 T+1 约束

        T+1 规则：当日买入的股票不能当日卖出，必须等到下一个交易日

        Args:
            order: 卖出订单
            portfolio: 投资组合
            current_date: 当前日期

        Returns:
            ValidationResult: 验证结果
        """
        # 只验证卖出订单
        if order.side != OrderSide.SELL:
            return ValidationResult(is_valid=True)

        # 获取持仓
        position = portfolio.get_position(order.symbol)
        if not position:
            return ValidationResult(
                is_valid=False,
                errors=[f"没有 {order.symbol} 的持仓，无法卖出"]
            )

        # T+1 检查：买入日期必须早于当前日期
        buy_date_normalized = datetime(
            position.buy_date.year,
            position.buy_date.month,
            position.buy_date.day
        )
        current_date_normalized = datetime(
            current_date.year,
            current_date.month,
            current_date.day
        )

        if buy_date_normalized >= current_date_normalized:
            logger.debug(
                f"T+1 violation: {order.symbol} bought on {position.buy_date.date()}, "
                f"cannot sell on {current_date.date()}"
            )
            return ValidationResult(
                is_valid=False,
                errors=[f"T+1 限制：{order.symbol} 于 {position.buy_date.date()} 买入，"
                       f"不能在 {current_date.date()} 卖出"]
            )

        return ValidationResult(is_valid=True)

    def _validate_price_limit(
        self,
        order: Order,
        market_data: MarketData,
        stock_info: Optional[StockInfo] = None
    ) -> ValidationResult:
        """
        验证涨跌停限制

        Args:
            order: 订单
            market_data: 市场数据
            stock_info: 股票信息（用于判断是否为新股）

        Returns:
            ValidationResult: 验证结果
        """
        # 获取涨跌停价格
        price_limits = self.get_price_limits(
            prev_close=market_data.prev_close,
            board=market_data.board_type,
            stock_info=stock_info,
            current_date=market_data.date
        )

        # 如果没有涨跌停限制（如港股、美股），直接通过
        if not price_limits.has_limit:
            return ValidationResult(is_valid=True)

        # 买入订单：检查是否涨停
        if order.side == OrderSide.BUY:
            if market_data.is_limit_up:
                logger.debug(f"{order.symbol} hit upper limit on {market_data.date.date()}")
                return ValidationResult(
                    is_valid=False,
                    errors=[f"{order.symbol} 涨停，无法买入"]
                )

        # 卖出订单：检查是否跌停
        elif order.side == OrderSide.SELL:
            if market_data.is_limit_down:
                logger.debug(f"{order.symbol} hit lower limit on {market_data.date.date()}")
                return ValidationResult(
                    is_valid=False,
                    errors=[f"{order.symbol} 跌停，无法卖出"]
                )

        return ValidationResult(is_valid=True)

    def _validate_balance(
        self,
        order: Order,
        portfolio: Portfolio
    ) -> ValidationResult:
        """
        验证资金/持仓是否充足

        Args:
            order: 订单
            portfolio: 投资组合

        Returns:
            ValidationResult: 验证结果
        """
        if order.side == OrderSide.BUY:
            # 买入：检查资金是否充足（粗略估算，不考虑手续费）
            required_amount = order.quantity * order.limit_price
            if portfolio.cash < required_amount:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"资金不足：需要 {required_amount:.2f}，可用 {portfolio.cash:.2f}"]
                )

        elif order.side == OrderSide.SELL:
            # 卖出：检查持仓是否充足
            position = portfolio.get_position(order.symbol)
            if not position or position.quantity < order.quantity:
                available = position.quantity if position else 0
                return ValidationResult(
                    is_valid=False,
                    errors=[f"持仓不足：需要 {order.quantity} 股，可用 {available} 股"]
                )

        return ValidationResult(is_valid=True)

    def get_price_limits(
        self,
        prev_close: float,
        board: str,
        stock_info: Optional[StockInfo] = None,
        current_date: Optional[datetime] = None
    ) -> PriceLimits:
        """
        计算涨跌停价格

        根据板块和股票信息计算涨跌停价格。
        考虑特殊情况：新股上市前N日无涨跌停限制。

        Args:
            prev_close: 昨收价
            board: 板块类型
            stock_info: 股票信息
            current_date: 当前日期

        Returns:
            PriceLimits: 涨跌停价格
        """
        # 获取板块规则
        if board not in self.price_limit_rules:
            logger.warning(f"Unknown board: {board}, using MAIN rules")
            board = 'MAIN'

        up_limit_pct, down_limit_pct = self.price_limit_rules[board]

        # 如果没有涨跌停限制（港股、美股）
        if up_limit_pct is None or down_limit_pct is None:
            return PriceLimits(
                upper_limit=None,
                lower_limit=None,
                has_limit=False
            )

        # 检查新股特殊规则
        if self._is_ipo_exception(stock_info, current_date, board):
            logger.debug(f"{stock_info.symbol} is in IPO exception period, no price limits")
            return PriceLimits(
                upper_limit=None,
                lower_limit=None,
                has_limit=False
            )

        # 计算涨跌停价格（四舍五入到分）
        upper_limit = round(prev_close * (1 + up_limit_pct), 2)
        lower_limit = round(prev_close * (1 - down_limit_pct), 2)

        return PriceLimits(
            upper_limit=upper_limit,
            lower_limit=lower_limit,
            has_limit=True
        )

    def _is_ipo_exception(
        self,
        stock_info: Optional[StockInfo],
        current_date: Optional[datetime],
        board: str
    ) -> bool:
        """
        判断是否为新股上市特殊期

        创业板/科创板：前5个交易日无涨跌停
        主板：首日涨幅限制44%（这里简化处理为无限制）

        Args:
            stock_info: 股票信息
            current_date: 当前日期
            board: 板块

        Returns:
            bool: 是否在特殊期
        """
        if not stock_info or not stock_info.ipo_date or not current_date:
            return False

        # 创业板和科创板前5个交易日
        if board in ['GEM', 'STAR']:
            ipo_days = 5
        # 主板首日（简化处理）
        elif board == 'MAIN':
            ipo_days = 1
        else:
            return False

        # 计算上市以来的交易日数量
        trading_days = self.calendar.get_trading_days_between(
            stock_info.ipo_date,
            current_date,
            inclusive=True
        )

        if len(trading_days) <= ipo_days:
            logger.debug(
                f"{stock_info.symbol} IPO on {stock_info.ipo_date.date()}, "
                f"trading day {len(trading_days)}/{ipo_days}"
            )
            return True

        return False

    def __repr__(self) -> str:
        return f"TradingRulesValidator(env={self.environment})"


# ==================== 规则工厂 ====================

class TradingRulesFactory:
    """
    交易规则工厂

    缓存和提供交易规则验证器实例
    """

    _cache: Dict[str, TradingRulesValidator] = {}

    @classmethod
    def get_validator(cls, environment: TradingEnvironment) -> TradingRulesValidator:
        """
        获取规则验证器实例（带缓存）

        Args:
            environment: 交易环境

        Returns:
            TradingRulesValidator: 规则验证器
        """
        env_key = str(environment)

        if env_key not in cls._cache:
            cls._cache[env_key] = TradingRulesValidator(environment)
            logger.info(f"Created TradingRulesValidator for {env_key}")

        return cls._cache[env_key]

    @classmethod
    def clear_cache(cls):
        """清空缓存"""
        cls._cache.clear()
        logger.info("Cleared TradingRulesValidator cache")
