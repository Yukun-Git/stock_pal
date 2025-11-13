"""
测试数据模型

测试 models.py 中定义的所有数据类
"""

import pytest
from datetime import datetime

from app.backtest.models import (
    Order, OrderSide, OrderStatus,
    Trade, Position, MarketData,
    TradingEnvironment, Portfolio,
    BacktestConfig, ValidationResult,
    PriceLimits, Commission
)


class TestTradingEnvironment:
    """测试交易环境"""

    def test_create_environment(self):
        """测试创建交易环境"""
        env = TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')
        assert env.market == 'CN'
        assert env.board == 'MAIN'
        assert env.channel == 'DIRECT'

    def test_environment_string_representation(self):
        """测试环境字符串表示"""
        # 直接交易（省略DIRECT）
        env1 = TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')
        assert str(env1) == 'CN_MAIN'

        # 港股通（包含CONNECT）
        env2 = TradingEnvironment(market='HK', board='MAIN', channel='CONNECT')
        assert str(env2) == 'HK_MAIN_CONNECT'

    def test_environment_immutable(self):
        """测试环境不可变性"""
        env = TradingEnvironment(market='CN', board='MAIN')
        with pytest.raises(Exception):  # dataclass frozen
            env.market = 'HK'


class TestOrder:
    """测试订单"""

    def test_create_order(self, sample_order_buy):
        """测试创建订单"""
        assert sample_order_buy.order_id == 'TEST_BUY_001'
        assert sample_order_buy.symbol == '600000'
        assert sample_order_buy.side == OrderSide.BUY
        assert sample_order_buy.quantity == 100
        assert sample_order_buy.limit_price == 10.50

    def test_order_repr(self, sample_order_buy):
        """测试订单字符串表示"""
        repr_str = repr(sample_order_buy)
        assert 'buy' in repr_str.lower()
        assert '600000' in repr_str
        assert '100' in repr_str


class TestTrade:
    """测试成交记录"""

    def test_create_trade(self, sample_trade):
        """测试创建成交记录"""
        assert sample_trade.trade_id == 'TRADE_001'
        assert sample_trade.symbol == '600000'
        assert sample_trade.quantity == 100
        assert sample_trade.price == 10.50

    def test_trade_total_cost(self, sample_trade):
        """测试成交总成本"""
        # amount=1050, commission=5, stamp_tax=0
        assert sample_trade.total_cost == 1055.0

    def test_trade_with_stamp_tax(self):
        """测试含印花税的成交"""
        trade = Trade(
            trade_id='TRADE_002',
            order_id='ORDER_002',
            symbol='600000',
            side=OrderSide.SELL,
            quantity=100,
            price=11.0,
            amount=1100.0,
            commission=5.0,
            stamp_tax=1.1,  # 0.1% 印花税
            executed_at=datetime(2024, 1, 16)
        )
        # amount=1100, commission=5, stamp_tax=1.1
        assert trade.total_cost == 1106.1


class TestPosition:
    """测试持仓"""

    def test_create_position(self, sample_position):
        """测试创建持仓"""
        assert sample_position.symbol == '600000'
        assert sample_position.quantity == 100
        assert sample_position.avg_cost == 10.50

    def test_position_market_value(self, sample_position):
        """测试持仓市值"""
        # quantity=100, current_price=11.20
        assert sample_position.market_value == 1120.0

    def test_position_cost_basis(self, sample_position):
        """测试持仓成本"""
        # quantity=100, avg_cost=10.50
        assert sample_position.cost_basis == 1050.0

    def test_position_unrealized_pnl(self, sample_position):
        """测试未实现盈亏"""
        # market_value=1120, cost_basis=1050
        assert sample_position.unrealized_pnl == 70.0

    def test_position_unrealized_pnl_pct(self, sample_position):
        """测试未实现盈亏率"""
        # unrealized_pnl=70, cost_basis=1050
        expected = 70.0 / 1050.0
        assert abs(sample_position.unrealized_pnl_pct - expected) < 0.0001


class TestPortfolio:
    """测试投资组合"""

    def test_create_portfolio(self):
        """测试创建投资组合"""
        portfolio = Portfolio(cash=100000)
        assert portfolio.cash == 100000
        assert portfolio.initial_capital == 100000
        assert len(portfolio.positions) == 0

    def test_portfolio_total_equity(self, sample_position):
        """测试总权益"""
        portfolio = Portfolio(cash=90000)
        portfolio.positions['600000'] = sample_position

        # cash=90000, market_value=1120
        assert portfolio.total_equity == 91120.0

    def test_portfolio_total_return(self, sample_position):
        """测试总收益"""
        portfolio = Portfolio(cash=90000, initial_capital=100000)
        portfolio.positions['600000'] = sample_position

        # total_equity=91120, initial_capital=100000
        assert portfolio.total_return == -8880.0

    def test_portfolio_has_position(self, sample_position):
        """测试是否持有股票"""
        portfolio = Portfolio(cash=100000)
        assert not portfolio.has_position('600000')

        portfolio.positions['600000'] = sample_position
        assert portfolio.has_position('600000')


class TestValidationResult:
    """测试验证结果"""

    def test_valid_result(self):
        """测试有效结果"""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert bool(result) is True
        assert len(result.errors) == 0

    def test_invalid_result(self):
        """测试无效结果"""
        result = ValidationResult(
            is_valid=False,
            errors=['Error 1', 'Error 2']
        )
        assert not result.is_valid
        assert bool(result) is False
        assert len(result.errors) == 2
        assert 'Error 1' in result.error_message


class TestPriceLimits:
    """测试涨跌停价格"""

    def test_price_limits_with_limit(self):
        """测试有涨跌停限制"""
        limits = PriceLimits(
            upper_limit=11.0,
            lower_limit=9.0,
            has_limit=True
        )
        assert limits.has_limit
        assert limits.upper_limit == 11.0
        assert limits.lower_limit == 9.0

    def test_price_limits_no_limit(self):
        """测试无涨跌停限制（港股）"""
        limits = PriceLimits(
            upper_limit=None,
            lower_limit=None,
            has_limit=False
        )
        assert not limits.has_limit
        assert limits.upper_limit is None


class TestCommission:
    """测试手续费"""

    def test_commission_total(self):
        """测试手续费总额"""
        commission = Commission(
            broker_fee=5.0,
            stamp_tax=1.0,
            transfer_fee=0.5
        )
        assert commission.total == 6.5

    def test_commission_with_currency_fee(self):
        """测试含货币兑换费（港股通）"""
        commission = Commission(
            broker_fee=9.0,
            stamp_tax=39.0,
            settlement_fee=0.6,
            currency_fee=3.0
        )
        assert commission.total == 51.6
