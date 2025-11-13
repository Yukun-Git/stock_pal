"""
测试交易规则验证器

测试 validator.py 的所有功能
"""

import pytest
from datetime import datetime, timedelta

from app.backtest.rules.validator import TradingRulesValidator, TradingRulesFactory
from app.backtest.models import (
    Order, OrderSide, OrderStatus, MarketData, Portfolio, Position,
    TradingEnvironment, StockInfo
)


class TestTradingRulesValidator:
    """测试交易规则验证器"""

    @pytest.fixture
    def validator_cn_main(self):
        """A股主板验证器"""
        env = TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')
        return TradingRulesValidator(env)

    @pytest.fixture
    def validator_cn_gem(self):
        """A股创业板验证器"""
        env = TradingEnvironment(market='CN', board='GEM', channel='DIRECT')
        return TradingRulesValidator(env)

    @pytest.fixture
    def sample_market_data_normal(self):
        """正常交易日的市场数据"""
        return MarketData(
            symbol='600000',
            date=datetime(2024, 1, 15, 9, 30, 0),
            open=10.30,
            high=10.80,
            low=10.20,
            close=10.50,
            volume=1000000,
            prev_close=10.00,
            is_suspended=False,
            is_limit_up=False,
            is_limit_down=False,
            board_type='MAIN'
        )

    @pytest.fixture
    def sample_market_data_limit_up(self):
        """涨停的市场数据"""
        return MarketData(
            symbol='600000',
            date=datetime(2024, 1, 15, 9, 30, 0),
            open=11.00,
            high=11.00,
            low=11.00,
            close=11.00,
            volume=500000,
            prev_close=10.00,
            is_suspended=False,
            is_limit_up=True,
            is_limit_down=False,
            board_type='MAIN'
        )

    @pytest.fixture
    def sample_market_data_suspended(self):
        """停牌的市场数据"""
        return MarketData(
            symbol='600000',
            date=datetime(2024, 1, 15, 9, 30, 0),
            open=10.00,
            high=10.00,
            low=10.00,
            close=10.00,
            volume=0,
            prev_close=10.00,
            is_suspended=True,
            is_limit_up=False,
            is_limit_down=False,
            board_type='MAIN'
        )

    def test_create_validator(self, validator_cn_main):
        """测试创建验证器"""
        assert validator_cn_main.environment.market == 'CN'
        assert validator_cn_main.environment.board == 'MAIN'
        assert validator_cn_main.calendar is not None

    def test_load_price_limit_rules(self, validator_cn_main, validator_cn_gem):
        """测试加载涨跌停规则"""
        # 主板 ±10%
        assert validator_cn_main.price_limit_rules['MAIN'] == (0.10, 0.10)

        # 创业板 ±20%
        assert validator_cn_gem.price_limit_rules['GEM'] == (0.20, 0.20)

    def test_validate_not_suspended(
        self,
        validator_cn_main,
        sample_market_data_normal,
        sample_market_data_suspended
    ):
        """测试停牌检查"""
        order = Order(
            order_id='TEST_001',
            symbol='600000',
            side=OrderSide.BUY,
            quantity=100,
            limit_price=10.50,
            created_at=datetime(2024, 1, 15, 9, 30, 0)
        )

        # 正常交易日
        assert validator_cn_main._validate_not_suspended(order, sample_market_data_normal)

        # 停牌
        assert not validator_cn_main._validate_not_suspended(order, sample_market_data_suspended)

    def test_validate_t_plus_1_buy(self, validator_cn_main):
        """测试T+1约束（买入订单不受限制）"""
        order = Order(
            order_id='TEST_001',
            symbol='600000',
            side=OrderSide.BUY,
            quantity=100,
            limit_price=10.50,
            created_at=datetime(2024, 1, 15, 9, 30, 0)
        )

        portfolio = Portfolio(cash=100000)
        current_date = datetime(2024, 1, 15)

        result = validator_cn_main._validate_t_plus_1(order, portfolio, current_date)
        assert result.is_valid

    def test_validate_t_plus_1_sell_same_day(self, validator_cn_main):
        """测试T+1约束（当日卖出违规）"""
        buy_date = datetime(2024, 1, 15)

        order = Order(
            order_id='TEST_001',
            symbol='600000',
            side=OrderSide.SELL,
            quantity=100,
            limit_price=11.00,
            created_at=datetime(2024, 1, 15, 9, 30, 0)
        )

        portfolio = Portfolio(cash=100000)
        portfolio.positions['600000'] = Position(
            symbol='600000',
            quantity=100,
            avg_cost=10.00,
            current_price=11.00,
            buy_date=buy_date
        )

        # 当日卖出（违规）
        result = validator_cn_main._validate_t_plus_1(order, portfolio, buy_date)
        assert not result.is_valid
        assert 'T+1' in result.error_message

    def test_validate_t_plus_1_sell_next_day(self, validator_cn_main):
        """测试T+1约束（次日卖出合规）"""
        buy_date = datetime(2024, 1, 15)
        sell_date = datetime(2024, 1, 16)

        order = Order(
            order_id='TEST_001',
            symbol='600000',
            side=OrderSide.SELL,
            quantity=100,
            limit_price=11.00,
            created_at=sell_date
        )

        portfolio = Portfolio(cash=100000)
        portfolio.positions['600000'] = Position(
            symbol='600000',
            quantity=100,
            avg_cost=10.00,
            current_price=11.00,
            buy_date=buy_date
        )

        # 次日卖出（合规）
        result = validator_cn_main._validate_t_plus_1(order, portfolio, sell_date)
        assert result.is_valid

    def test_validate_price_limit_buy_limit_up(
        self,
        validator_cn_main,
        sample_market_data_limit_up
    ):
        """测试涨停限制（涨停无法买入）"""
        order = Order(
            order_id='TEST_001',
            symbol='600000',
            side=OrderSide.BUY,
            quantity=100,
            limit_price=11.00,
            created_at=datetime(2024, 1, 15, 9, 30, 0)
        )

        result = validator_cn_main._validate_price_limit(
            order, sample_market_data_limit_up
        )
        assert not result.is_valid
        assert '涨停' in result.error_message

    def test_validate_balance_buy_insufficient_funds(self, validator_cn_main):
        """测试资金不足"""
        order = Order(
            order_id='TEST_001',
            symbol='600000',
            side=OrderSide.BUY,
            quantity=1000,
            limit_price=100.00,
            created_at=datetime(2024, 1, 15, 9, 30, 0)
        )

        portfolio = Portfolio(cash=10000)  # 资金不足

        result = validator_cn_main._validate_balance(order, portfolio)
        assert not result.is_valid
        assert '资金不足' in result.error_message

    def test_validate_balance_sell_insufficient_position(self, validator_cn_main):
        """测试持仓不足"""
        order = Order(
            order_id='TEST_001',
            symbol='600000',
            side=OrderSide.SELL,
            quantity=200,
            limit_price=11.00,
            created_at=datetime(2024, 1, 15, 9, 30, 0)
        )

        portfolio = Portfolio(cash=100000)
        portfolio.positions['600000'] = Position(
            symbol='600000',
            quantity=100,  # 持仓不足
            avg_cost=10.00,
            current_price=11.00,
            buy_date=datetime(2024, 1, 14)
        )

        result = validator_cn_main._validate_balance(order, portfolio)
        assert not result.is_valid
        assert '持仓不足' in result.error_message

    def test_get_price_limits_main_board(self, validator_cn_main):
        """测试获取主板涨跌停价格"""
        price_limits = validator_cn_main.get_price_limits(
            prev_close=10.00,
            board='MAIN'
        )

        assert price_limits.has_limit
        assert price_limits.upper_limit == 11.00  # +10%
        assert price_limits.lower_limit == 9.00   # -10%

    def test_get_price_limits_gem_board(self, validator_cn_gem):
        """测试获取创业板涨跌停价格"""
        price_limits = validator_cn_gem.get_price_limits(
            prev_close=20.00,
            board='GEM'
        )

        assert price_limits.has_limit
        assert price_limits.upper_limit == 24.00  # +20%
        assert price_limits.lower_limit == 16.00  # -20%

    def test_get_price_limits_st_stock(self, validator_cn_main):
        """测试获取ST股票涨跌停价格"""
        price_limits = validator_cn_main.get_price_limits(
            prev_close=10.00,
            board='ST'
        )

        assert price_limits.has_limit
        assert price_limits.upper_limit == 10.50  # +5%
        assert price_limits.lower_limit == 9.50   # -5%

    def test_get_price_limits_ipo_exception(self, validator_cn_gem):
        """测试新股上市特殊期无涨跌停"""
        ipo_date = datetime(2024, 1, 10)
        current_date = datetime(2024, 1, 12)  # IPO后第2个交易日

        stock_info = StockInfo(
            symbol='300999',
            name='测试新股',
            board='GEM',
            ipo_date=ipo_date
        )

        price_limits = validator_cn_gem.get_price_limits(
            prev_close=50.00,
            board='GEM',
            stock_info=stock_info,
            current_date=current_date
        )

        # 创业板前5日无涨跌停
        assert not price_limits.has_limit
        assert price_limits.upper_limit is None
        assert price_limits.lower_limit is None

    def test_validate_order_complete(
        self,
        validator_cn_main,
        sample_market_data_normal
    ):
        """测试完整订单验证"""
        buy_date = datetime(2024, 1, 14)
        current_date = datetime(2024, 1, 15)

        order = Order(
            order_id='TEST_001',
            symbol='600000',
            side=OrderSide.SELL,
            quantity=100,
            limit_price=10.50,
            created_at=current_date
        )

        portfolio = Portfolio(cash=100000)
        portfolio.positions['600000'] = Position(
            symbol='600000',
            quantity=100,
            avg_cost=10.00,
            current_price=10.50,
            buy_date=buy_date
        )

        result = validator_cn_main.validate_order(
            order,
            sample_market_data_normal,
            portfolio,
            current_date
        )

        assert result.is_valid
        assert len(result.errors) == 0


class TestTradingRulesFactory:
    """测试交易规则工厂"""

    def test_get_validator_cached(self):
        """测试获取验证器（缓存）"""
        env = TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')

        validator1 = TradingRulesFactory.get_validator(env)
        validator2 = TradingRulesFactory.get_validator(env)

        # 应该是同一个实例
        assert validator1 is validator2

    def test_clear_cache(self):
        """测试清空缓存"""
        env = TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')

        validator1 = TradingRulesFactory.get_validator(env)
        TradingRulesFactory.clear_cache()
        validator2 = TradingRulesFactory.get_validator(env)

        # 清空后应该是不同实例
        assert validator1 is not validator2
