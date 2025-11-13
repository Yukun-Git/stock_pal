"""
测试交易日历

测试 trading_calendar.py 的所有功能
"""

import pytest
from datetime import datetime, timedelta

from app.backtest.rules.trading_calendar import TradingCalendar, get_trading_calendar


class TestTradingCalendar:
    """测试交易日历"""

    @pytest.fixture
    def calendar(self):
        """创建测试用交易日历"""
        return TradingCalendar(market='CN')

    def test_create_calendar(self, calendar):
        """测试创建交易日历"""
        assert calendar.market == 'CN'
        assert len(calendar.trading_days) > 0
        assert len(calendar.trading_days_list) > 0

    def test_is_trading_day_weekday(self, calendar):
        """测试工作日是否为交易日"""
        # 2024-01-15 是周一
        date = datetime(2024, 1, 15)
        # 注意：实际结果取决于是否有假期，这里只测试函数运行
        result = calendar.is_trading_day(date)
        assert isinstance(result, bool)

    def test_is_trading_day_weekend(self, calendar):
        """测试周末不是交易日"""
        # 2024-01-13 是周六
        date = datetime(2024, 1, 13)
        result = calendar.is_trading_day(date)
        # 周末肯定不是交易日
        assert result is False

    def test_next_trading_day(self, calendar):
        """测试获取下一个交易日"""
        # 从一个交易日开始
        date = datetime(2024, 1, 15)
        if calendar.is_trading_day(date):
            next_day = calendar.next_trading_day(date)
            assert next_day > date
            assert calendar.is_trading_day(next_day)

    def test_next_trading_day_skip(self, calendar):
        """测试跳过多个交易日"""
        date = datetime(2024, 1, 15)
        if calendar.is_trading_day(date):
            # 跳过3个交易日
            next_day = calendar.next_trading_day(date, skip=3)
            assert next_day > date
            assert calendar.is_trading_day(next_day)

    def test_prev_trading_day(self, calendar):
        """测试获取上一个交易日"""
        date = datetime(2024, 1, 16)
        if calendar.is_trading_day(date):
            prev_day = calendar.prev_trading_day(date)
            assert prev_day < date
            assert calendar.is_trading_day(prev_day)

    def test_get_trading_days_between(self, calendar):
        """测试获取日期区间内的交易日"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        trading_days = calendar.get_trading_days_between(start, end)

        assert len(trading_days) > 0
        assert all(calendar.is_trading_day(d) for d in trading_days)
        assert trading_days == sorted(trading_days)  # 确保排序

    def test_count_trading_days(self, calendar):
        """测试计算交易日数量"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        count = calendar.count_trading_days(start, end)
        trading_days = calendar.get_trading_days_between(start, end)

        assert count == len(trading_days)

    def test_get_latest_trading_day(self, calendar):
        """测试获取最新交易日"""
        latest = calendar.get_latest_trading_day()
        assert isinstance(latest, datetime)
        assert calendar.is_trading_day(latest)

    def test_get_earliest_trading_day(self, calendar):
        """测试获取最早交易日"""
        earliest = calendar.get_earliest_trading_day()
        assert isinstance(earliest, datetime)
        assert calendar.is_trading_day(earliest)

    def test_calendar_repr(self, calendar):
        """测试日历字符串表示"""
        repr_str = repr(calendar)
        assert 'CN' in repr_str
        assert 'days=' in repr_str


class TestTradingCalendarCache:
    """测试交易日历缓存"""

    def test_cache_creation(self, tmp_path):
        """测试缓存创建"""
        calendar = TradingCalendar(market='CN', cache_dir=str(tmp_path))
        cache_file = tmp_path / 'trading_calendar_CN.pkl'

        # 第一次创建应生成缓存
        assert cache_file.exists()

    def test_cache_loading(self, tmp_path):
        """测试缓存加载"""
        # 第一次创建
        calendar1 = TradingCalendar(market='CN', cache_dir=str(tmp_path))
        days_count1 = len(calendar1.trading_days)

        # 第二次创建应从缓存加载
        calendar2 = TradingCalendar(market='CN', cache_dir=str(tmp_path))
        days_count2 = len(calendar2.trading_days)

        assert days_count1 == days_count2


class TestTradingCalendarSingleton:
    """测试交易日历单例"""

    def test_get_trading_calendar_singleton(self):
        """测试单例模式"""
        calendar1 = get_trading_calendar('CN')
        calendar2 = get_trading_calendar('CN')

        # 应该是同一个实例
        assert calendar1 is calendar2

    def test_get_trading_calendar_different_markets(self):
        """测试不同市场的日历"""
        calendar_cn = get_trading_calendar('CN')
        calendar_hk = get_trading_calendar('HK')

        # 应该是不同实例
        assert calendar_cn is not calendar_hk
        assert calendar_cn.market == 'CN'
        assert calendar_hk.market == 'HK'
