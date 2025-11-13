"""
测试撮合引擎

测试 matching_engine.py 的所有功能
"""

import pytest
from datetime import datetime

from app.backtest.matching_engine import MatchingEngine
from app.backtest.models import (
    Order, OrderSide, OrderStatus, MarketData, StockInfo,
    TradingEnvironment
)


class TestMatchingEngine:
    """测试撮合引擎"""

    @pytest.fixture
    def engine_cn_main(self):
        """A股主板撮合引擎"""
        env = TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')
        return MatchingEngine(
            environment=env,
            slippage_bps=5.0,
            commission_rate=0.0003,
            min_commission=5.0,
            stamp_tax_rate=0.001
        )

    @pytest.fixture
    def sample_market_data(self):
        """正常市场数据"""
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
        """涨停市场数据"""
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
        """停牌市场数据"""
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

    @pytest.fixture
    def buy_order(self):
        """买入订单"""
        return Order(
            order_id='TEST_BUY_001',
            symbol='600000',
            side=OrderSide.BUY,
            quantity=100,
            limit_price=10.50,
            created_at=datetime(2024, 1, 15, 9, 30, 0)
        )

    @pytest.fixture
    def sell_order(self):
        """卖出订单"""
        return Order(
            order_id='TEST_SELL_001',
            symbol='600000',
            side=OrderSide.SELL,
            quantity=100,
            limit_price=10.50,
            created_at=datetime(2024, 1, 15, 9, 30, 0)
        )

    def test_create_engine(self, engine_cn_main):
        """测试创建撮合引擎"""
        assert engine_cn_main.environment.market == 'CN'
        assert engine_cn_main.slippage_bps == 5.0
        assert engine_cn_main.commission_rate == 0.0003

    def test_match_order_buy_success(
        self,
        engine_cn_main,
        buy_order,
        sample_market_data
    ):
        """测试买入订单撮合成功"""
        trade = engine_cn_main.match_order(buy_order, sample_market_data)

        assert trade is not None
        assert trade.symbol == '600000'
        assert trade.side == OrderSide.BUY
        assert trade.quantity == 100
        # 买入价格应该是 close + 滑点
        # close=10.50, slippage=5bp, expected=10.50*1.0005=10.50525, rounded=10.51
        assert trade.price > sample_market_data.close
        assert trade.commission > 0

    def test_match_order_sell_success(
        self,
        engine_cn_main,
        sell_order,
        sample_market_data
    ):
        """测试卖出订单撮合成功"""
        trade = engine_cn_main.match_order(sell_order, sample_market_data)

        assert trade is not None
        assert trade.symbol == '600000'
        assert trade.side == OrderSide.SELL
        assert trade.quantity == 100
        # 卖出价格应该是 close - 滑点
        assert trade.price < sample_market_data.close
        # 卖出应该有印花税
        assert trade.stamp_tax > 0

    def test_match_order_suspended(
        self,
        engine_cn_main,
        buy_order,
        sample_market_data_suspended
    ):
        """测试停牌无法成交"""
        trade = engine_cn_main.match_order(buy_order, sample_market_data_suspended)

        assert trade is None

    def test_match_order_limit_up_cannot_buy(
        self,
        engine_cn_main,
        buy_order,
        sample_market_data_limit_up
    ):
        """测试涨停无法买入"""
        trade = engine_cn_main.match_order(buy_order, sample_market_data_limit_up)

        assert trade is None

    def test_calculate_execution_price_buy(
        self,
        engine_cn_main,
        buy_order,
        sample_market_data
    ):
        """测试买入成交价格计算"""
        price = engine_cn_main._calculate_execution_price(
            buy_order, sample_market_data
        )

        # 买入：向上滑点
        # close=10.50, slippage=5bp, expected=10.50525
        assert price > sample_market_data.close
        assert price == pytest.approx(10.51, abs=0.01)

    def test_calculate_execution_price_sell(
        self,
        engine_cn_main,
        sell_order,
        sample_market_data
    ):
        """测试卖出成交价格计算"""
        price = engine_cn_main._calculate_execution_price(
            sell_order, sample_market_data
        )

        # 卖出：向下滑点
        # close=10.50, slippage=5bp, expected=10.49475
        assert price < sample_market_data.close
        assert price == pytest.approx(10.49, abs=0.01)

    def test_calculate_commission_buy(self, engine_cn_main, buy_order):
        """测试买入手续费计算"""
        amount = 1050.0  # 100股 * 10.50元

        commission = engine_cn_main._calculate_commission(buy_order, amount)

        # 券商佣金: 1050 * 0.0003 = 0.315, 但最低5元
        assert commission.broker_fee == 5.0
        # 买入无印花税
        assert commission.stamp_tax == 0.0
        # 总费用
        assert commission.total >= 5.0

    def test_calculate_commission_sell(self, engine_cn_main, sell_order):
        """测试卖出手续费计算"""
        amount = 1050.0  # 100股 * 10.50元

        commission = engine_cn_main._calculate_commission(sell_order, amount)

        # 券商佣金: 1050 * 0.0003 = 0.315, 但最低5元
        assert commission.broker_fee == 5.0
        # 印花税: 1050 * 0.001 = 1.05
        assert commission.stamp_tax == 1.05
        # 总费用 = 佣金 + 印花税
        assert commission.total >= 6.0

    def test_calculate_commission_shanghai_stock(self, engine_cn_main):
        """测试上海股票手续费（含过户费）"""
        order = Order(
            order_id='TEST_001',
            symbol='600000',  # 上海股票
            side=OrderSide.BUY,
            quantity=1000,
            limit_price=10.00,
            created_at=datetime.now()
        )

        amount = 10000.0

        commission = engine_cn_main._calculate_commission(order, amount)

        # 应该包含过户费
        assert commission.transfer_fee > 0
        assert commission.transfer_fee == pytest.approx(10000 * 0.00002, abs=0.01)

    def test_calculate_commission_shenzhen_stock(self, engine_cn_main):
        """测试深圳股票手续费（无过户费）"""
        order = Order(
            order_id='TEST_001',
            symbol='000001',  # 深圳股票
            side=OrderSide.BUY,
            quantity=1000,
            limit_price=10.00,
            created_at=datetime.now()
        )

        amount = 10000.0

        commission = engine_cn_main._calculate_commission(order, amount)

        # 深圳股票无过户费
        assert commission.transfer_fee == 0.0

    def test_set_slippage(self, engine_cn_main):
        """测试设置滑点"""
        engine_cn_main.set_slippage(10.0)
        assert engine_cn_main.slippage_bps == 10.0

    def test_set_commission_rate(self, engine_cn_main):
        """测试设置手续费率"""
        engine_cn_main.set_commission_rate(0.0005, 10.0)
        assert engine_cn_main.commission_rate == 0.0005
        assert engine_cn_main.min_commission == 10.0

    def test_generate_trade_id(self, engine_cn_main):
        """测试生成成交ID"""
        trade_id1 = engine_cn_main._generate_trade_id()
        trade_id2 = engine_cn_main._generate_trade_id()

        assert trade_id1.startswith('TRADE_')
        assert trade_id2.startswith('TRADE_')
        # 两个ID应该不同
        assert trade_id1 != trade_id2

    def test_match_order_with_stock_info(
        self,
        engine_cn_main,
        buy_order,
        sample_market_data
    ):
        """测试带股票信息的订单撮合"""
        stock_info = StockInfo(
            symbol='600000',
            name='浦发银行',
            board='MAIN',
            is_st=False
        )

        trade = engine_cn_main.match_order(
            buy_order,
            sample_market_data,
            stock_info
        )

        assert trade is not None
        assert trade.symbol == '600000'


class TestMatchingEngineHKConnect:
    """测试港股通撮合引擎"""

    @pytest.fixture
    def engine_hk_connect(self):
        """港股通撮合引擎"""
        env = TradingEnvironment(market='HK', board='MAIN', channel='CONNECT')
        return MatchingEngine(
            environment=env,
            slippage_bps=5.0,
            commission_rate=0.0003,
            min_commission=5.0
        )

    def test_commission_with_currency_fee(self, engine_hk_connect):
        """测试港股通手续费（含货币兑换费）"""
        order = Order(
            order_id='TEST_001',
            symbol='00700',
            side=OrderSide.BUY,
            quantity=100,
            limit_price=300.0,
            created_at=datetime.now()
        )

        amount = 30000.0

        commission = engine_hk_connect._calculate_commission(order, amount)

        # 港股通应该包含货币兑换费
        assert commission.currency_fee > 0
        assert commission.currency_fee == pytest.approx(30000 * 0.0001, abs=0.01)
        # 额外结算费
        assert commission.settlement_fee > 0
