"""
测试交易引擎

测试 trading_engine.py 的所有功能
"""

import pytest
from datetime import datetime

from app.backtest.trading_engine import TradingEngine
from app.backtest.models import (
    Signal, MarketData, TradingEnvironment, OrderSide
)


class TestTradingEngine:
    """测试交易引擎"""

    @pytest.fixture
    def engine(self):
        """创建测试用交易引擎"""
        env = TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')
        return TradingEngine(
            environment=env,
            initial_capital=100000,
            commission_rate=0.0003,
            min_commission=5.0,
            slippage_bps=5.0
        )

    @pytest.fixture
    def market_data_day1(self):
        """第1天市场数据"""
        return MarketData(
            symbol='600000',
            date=datetime(2024, 1, 15, 15, 0, 0),
            open=10.00,
            high=10.50,
            low=9.80,
            close=10.30,
            volume=1000000,
            prev_close=10.00,
            is_suspended=False,
            is_limit_up=False,
            is_limit_down=False,
            board_type='MAIN'
        )

    @pytest.fixture
    def market_data_day2(self):
        """第2天市场数据"""
        return MarketData(
            symbol='600000',
            date=datetime(2024, 1, 16, 15, 0, 0),
            open=10.30,
            high=11.00,
            low=10.20,
            close=10.80,
            volume=1200000,
            prev_close=10.30,
            is_suspended=False,
            is_limit_up=False,
            is_limit_down=False,
            board_type='MAIN'
        )

    def test_create_engine(self, engine):
        """测试创建交易引擎"""
        assert engine.initial_capital == 100000
        assert engine.portfolio.cash == 100000
        assert len(engine.trades) == 0
        assert len(engine.orders) == 0

    def test_process_buy_signal(self, engine, market_data_day1):
        """测试处理买入信号"""
        signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=1,  # 买入
            price=10.30
        )

        trade = engine.process_signal(signal, market_data_day1, datetime(2024, 1, 15))

        # 应该成交
        assert trade is not None
        assert trade.side == OrderSide.BUY
        assert trade.symbol == '600000'
        assert trade.quantity > 0

        # 检查持仓
        assert engine.portfolio.has_position('600000')
        position = engine.portfolio.get_position('600000')
        assert position.quantity == trade.quantity

        # 检查资金减少
        assert engine.portfolio.cash < engine.initial_capital

    def test_process_sell_signal_without_position(self, engine, market_data_day1):
        """测试没有持仓时卖出信号"""
        signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=-1,  # 卖出
            price=10.30
        )

        trade = engine.process_signal(signal, market_data_day1, datetime(2024, 1, 15))

        # 不应该成交（没有持仓）
        assert trade is None

    def test_process_complete_trade_cycle(self, engine, market_data_day1, market_data_day2):
        """测试完整的买卖周期"""
        # Day 1: 买入
        buy_signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=1,
            price=10.30
        )

        buy_trade = engine.process_signal(buy_signal, market_data_day1, datetime(2024, 1, 15))

        assert buy_trade is not None
        initial_quantity = buy_trade.quantity
        cash_after_buy = engine.portfolio.cash

        # Day 2: 卖出
        sell_signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 16),
            action=-1,
            price=10.80
        )

        sell_trade = engine.process_signal(sell_signal, market_data_day2, datetime(2024, 1, 16))

        assert sell_trade is not None
        assert sell_trade.side == OrderSide.SELL
        assert sell_trade.quantity == initial_quantity

        # 检查持仓已清空
        assert not engine.portfolio.has_position('600000')

        # 检查资金增加
        assert engine.portfolio.cash > cash_after_buy

    def test_t_plus_1_restriction(self, engine, market_data_day1):
        """测试T+1限制（当日买入不能当日卖出）"""
        # Day 1: 买入
        buy_signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=1,
            price=10.30
        )

        buy_trade = engine.process_signal(buy_signal, market_data_day1, datetime(2024, 1, 15))
        assert buy_trade is not None

        # Day 1: 尝试当日卖出
        sell_signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=-1,
            price=10.50
        )

        sell_trade = engine.process_signal(sell_signal, market_data_day1, datetime(2024, 1, 15))

        # 应该被拒绝（T+1限制）
        assert sell_trade is None
        assert engine.portfolio.has_position('600000')

    def test_hold_signal(self, engine, market_data_day1):
        """测试持有信号"""
        signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=0,  # 持有
            price=10.30
        )

        trade = engine.process_signal(signal, market_data_day1, datetime(2024, 1, 15))

        # 不应该有交易
        assert trade is None
        assert len(engine.trades) == 0

    def test_equity_tracking(self, engine, market_data_day1, market_data_day2):
        """测试权益跟踪"""
        initial_equity = engine.get_current_equity()
        assert initial_equity == 100000

        # Day 1: 买入
        buy_signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=1,
            price=10.30
        )

        engine.process_signal(buy_signal, market_data_day1, datetime(2024, 1, 15))

        # 权益应该略微下降（手续费）
        equity_after_buy = engine.get_current_equity()
        assert equity_after_buy < initial_equity

        # Day 2: 价格上涨后更新
        hold_signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 16),
            action=0,
            price=10.80
        )

        engine.process_signal(hold_signal, market_data_day2, datetime(2024, 1, 16))

        # 权益应该增加（价格上涨）
        equity_after_price_increase = engine.get_current_equity()
        assert equity_after_price_increase > equity_after_buy

    def test_get_statistics(self, engine, market_data_day1, market_data_day2):
        """测试获取统计信息"""
        # 执行一次买卖
        buy_signal = Signal(symbol='600000', date=datetime(2024, 1, 15), action=1, price=10.30)
        engine.process_signal(buy_signal, market_data_day1, datetime(2024, 1, 15))

        sell_signal = Signal(symbol='600000', date=datetime(2024, 1, 16), action=-1, price=10.80)
        engine.process_signal(sell_signal, market_data_day2, datetime(2024, 1, 16))

        stats = engine.get_statistics()

        assert stats['total_orders'] >= 2
        assert stats['total_trades'] >= 2
        assert stats['buy_trades'] >= 1
        assert stats['sell_trades'] >= 1
        assert stats['current_positions'] == 0
        assert 'current_cash' in stats
        assert 'total_return_pct' in stats

    def test_insufficient_funds(self, engine, market_data_day1):
        """测试资金不足"""
        # 设置引擎资金为很少
        engine.portfolio.cash = 100

        signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=1,
            price=10.30
        )

        trade = engine.process_signal(signal, market_data_day1, datetime(2024, 1, 15))

        # 应该无法买入（资金不足）
        assert trade is None

    def test_suspended_stock(self, engine):
        """测试停牌股票"""
        signal = Signal(
            symbol='600000',
            date=datetime(2024, 1, 15),
            action=1,
            price=10.30
        )

        market_data_suspended = MarketData(
            symbol='600000',
            date=datetime(2024, 1, 15),
            open=10.30,
            high=10.30,
            low=10.30,
            close=10.30,
            volume=0,
            prev_close=10.00,
            is_suspended=True,
            is_limit_up=False,
            is_limit_down=False,
            board_type='MAIN'
        )

        trade = engine.process_signal(signal, market_data_suspended, datetime(2024, 1, 15))

        # 停牌无法成交
        assert trade is None

    def test_get_total_return(self, engine, market_data_day1, market_data_day2):
        """测试总收益率"""
        initial_return = engine.get_total_return()
        assert initial_return == 0.0

        # 执行一次盈利的交易
        buy_signal = Signal(symbol='600000', date=datetime(2024, 1, 15), action=1, price=10.30)
        engine.process_signal(buy_signal, market_data_day1, datetime(2024, 1, 15))

        sell_signal = Signal(symbol='600000', date=datetime(2024, 1, 16), action=-1, price=10.80)
        engine.process_signal(sell_signal, market_data_day2, datetime(2024, 1, 16))

        final_return = engine.get_total_return()
        # 应该有正收益（价格上涨10.30 -> 10.80）
        assert final_return > 0
