"""
测试配置和共享 fixtures

提供测试中常用的数据和工具函数
"""

import pytest
from datetime import datetime
import pandas as pd

from app.backtest.models import (
    Order, OrderSide, OrderStatus,
    Trade, Position, MarketData,
    TradingEnvironment, BacktestConfig
)


@pytest.fixture
def sample_trading_environment():
    """示例交易环境（A股主板）"""
    return TradingEnvironment(market='CN', board='MAIN', channel='DIRECT')


@pytest.fixture
def sample_order_buy():
    """示例买入订单"""
    return Order(
        order_id='TEST_BUY_001',
        symbol='600000',
        side=OrderSide.BUY,
        quantity=100,
        limit_price=10.50,
        created_at=datetime(2024, 1, 15, 9, 30, 0),
        status=OrderStatus.PENDING
    )


@pytest.fixture
def sample_order_sell():
    """示例卖出订单"""
    return Order(
        order_id='TEST_SELL_001',
        symbol='600000',
        side=OrderSide.SELL,
        quantity=100,
        limit_price=11.20,
        created_at=datetime(2024, 1, 16, 9, 30, 0),
        status=OrderStatus.PENDING
    )


@pytest.fixture
def sample_trade():
    """示例成交记录"""
    return Trade(
        trade_id='TRADE_001',
        order_id='ORDER_001',
        symbol='600000',
        side=OrderSide.BUY,
        quantity=100,
        price=10.50,
        amount=1050.0,
        commission=5.0,
        stamp_tax=0.0,
        slippage=0.05,
        executed_at=datetime(2024, 1, 15, 9, 31, 0)
    )


@pytest.fixture
def sample_position():
    """示例持仓"""
    return Position(
        symbol='600000',
        quantity=100,
        avg_cost=10.50,
        current_price=11.20,
        buy_date=datetime(2024, 1, 15)
    )


@pytest.fixture
def sample_market_data():
    """示例市场数据"""
    return MarketData(
        symbol='600000',
        date=datetime(2024, 1, 15),
        open=10.30,
        high=10.80,
        low=10.20,
        close=10.50,
        volume=1000000,
        prev_close=10.00,
        is_suspended=False,
        is_limit_up=False,
        is_limit_down=False,
        board_type='MAIN',
        stock_name='浦发银行'
    )


@pytest.fixture
def sample_backtest_config():
    """示例回测配置"""
    return BacktestConfig(
        symbol='600000',
        start_date='20240101',
        end_date='20241231',
        initial_capital=100000,
        commission_rate=0.0003,
        min_commission=5.0,
        slippage_bps=5.0,
        stamp_tax_rate=0.001,
        strategy_id='ma_cross',
        strategy_params={'short_period': 10, 'long_period': 60}
    )


@pytest.fixture
def sample_price_data():
    """示例价格数据（DataFrame）"""
    dates = pd.date_range('2024-01-01', '2024-01-31', freq='B')  # 工作日
    data = {
        'date': dates,
        'open': [10.0 + i * 0.1 for i in range(len(dates))],
        'high': [10.2 + i * 0.1 for i in range(len(dates))],
        'low': [9.8 + i * 0.1 for i in range(len(dates))],
        'close': [10.1 + i * 0.1 for i in range(len(dates))],
        'volume': [1000000 + i * 10000 for i in range(len(dates))],
    }
    return pd.DataFrame(data)


# 测试辅助函数

def assert_order_valid(order: Order):
    """断言订单有效"""
    assert order.order_id is not None
    assert order.symbol is not None
    assert order.quantity > 0
    assert order.limit_price > 0
    assert order.created_at is not None


def assert_trade_valid(trade: Trade):
    """断言成交记录有效"""
    assert trade.trade_id is not None
    assert trade.order_id is not None
    assert trade.symbol is not None
    assert trade.quantity > 0
    assert trade.price > 0
    assert trade.amount > 0
    assert trade.executed_at is not None


def assert_position_valid(position: Position):
    """断言持仓有效"""
    assert position.symbol is not None
    assert position.quantity >= 0
    assert position.avg_cost >= 0
    assert position.current_price >= 0
    assert position.buy_date is not None
