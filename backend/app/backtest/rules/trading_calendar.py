"""
交易日历

管理交易日、非交易日的判断和计算。
支持多市场（中国、香港、美国）的交易日历。
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Set, Optional
import logging
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


class TradingCalendar:
    """
    交易日历

    功能：
    1. 判断是否为交易日
    2. 获取下一个/上一个交易日
    3. 获取日期区间内的所有交易日
    4. 支持多市场（目前实现中国A股）

    使用缓存机制提升性能。
    """

    def __init__(self, market: str = 'CN', cache_dir: Optional[str] = None):
        """
        初始化交易日历

        Args:
            market: 市场代码 ('CN', 'HK', 'US')
            cache_dir: 缓存目录，默认为 'data/cache'
        """
        self.market = market
        self.cache_dir = Path(cache_dir or 'data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.trading_days: Set[datetime] = set()
        self.trading_days_list: List[datetime] = []
        self._load_calendar()

    def _get_cache_path(self) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f'trading_calendar_{self.market}.pkl'

    def _load_from_cache(self) -> bool:
        """从缓存加载"""
        cache_path = self._get_cache_path()
        if not cache_path.exists():
            return False

        try:
            # 检查缓存是否过期（超过7天）
            cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if datetime.now() - cache_time > timedelta(days=7):
                logger.info(f"Trading calendar cache expired for {self.market}")
                return False

            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
                self.trading_days = data['trading_days']
                self.trading_days_list = data['trading_days_list']

            logger.info(f"Loaded {len(self.trading_days)} trading days from cache for {self.market}")
            return True

        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return False

    def _save_to_cache(self):
        """保存到缓存"""
        try:
            cache_path = self._get_cache_path()
            data = {
                'trading_days': self.trading_days,
                'trading_days_list': self.trading_days_list
            }
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Saved trading calendar cache for {self.market}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _load_calendar(self):
        """加载交易日历"""
        # 尝试从缓存加载
        if self._load_from_cache():
            return

        # 从数据源加载
        logger.info(f"Loading trading calendar for {self.market}...")

        if self.market == 'CN':
            self._load_cn_calendar()
        elif self.market == 'HK':
            self._load_hk_calendar()
        elif self.market == 'US':
            self._load_us_calendar()
        else:
            raise ValueError(f"Unsupported market: {self.market}")

        # 保存到缓存
        self._save_to_cache()

    def _load_cn_calendar(self):
        """加载中国A股交易日历"""
        try:
            # 使用 AkShare 获取交易日历
            df = ak.tool_trade_date_hist_sina()

            # 转换为 datetime 对象
            self.trading_days_list = pd.to_datetime(df['trade_date']).tolist()
            self.trading_days = set(self.trading_days_list)

            logger.info(f"Loaded {len(self.trading_days)} trading days for CN market")

        except Exception as e:
            logger.error(f"Failed to load CN trading calendar: {e}")
            # 回退到简单策略：周一到周五
            self._use_weekday_fallback()

    def _load_hk_calendar(self):
        """加载香港市场交易日历"""
        # TODO: 实现港股交易日历
        logger.warning("HK calendar not implemented, using weekday fallback")
        self._use_weekday_fallback()

    def _load_us_calendar(self):
        """加载美股交易日历"""
        # TODO: 实现美股交易日历
        logger.warning("US calendar not implemented, using weekday fallback")
        self._use_weekday_fallback()

    def _use_weekday_fallback(self):
        """回退策略：使用周一到周五作为交易日"""
        logger.warning("Using weekday fallback for trading calendar")
        start_date = datetime(2000, 1, 1)
        end_date = datetime(2030, 12, 31)

        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # 周一到周五
                self.trading_days.add(current)
                self.trading_days_list.append(current)
            current += timedelta(days=1)

        self.trading_days_list.sort()

    def is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为交易日

        Args:
            date: 日期

        Returns:
            bool: 是否为交易日
        """
        # 规范化日期（去除时分秒）
        date_normalized = datetime(date.year, date.month, date.day)
        return date_normalized in self.trading_days

    def next_trading_day(self, date: datetime, skip: int = 1) -> datetime:
        """
        获取下一个交易日

        Args:
            date: 起始日期
            skip: 跳过的交易日数量（默认1，即下一个）

        Returns:
            datetime: 下一个交易日
        """
        date_normalized = datetime(date.year, date.month, date.day)
        next_date = date_normalized + timedelta(days=1)

        count = 0
        while True:
            if next_date in self.trading_days:
                count += 1
                if count == skip:
                    return next_date
            next_date += timedelta(days=1)

            # 防止无限循环
            if (next_date - date_normalized).days > 365:
                raise ValueError(f"Cannot find next trading day after {date}")

    def prev_trading_day(self, date: datetime, skip: int = 1) -> datetime:
        """
        获取上一个交易日

        Args:
            date: 起始日期
            skip: 跳过的交易日数量（默认1，即上一个）

        Returns:
            datetime: 上一个交易日
        """
        date_normalized = datetime(date.year, date.month, date.day)
        prev_date = date_normalized - timedelta(days=1)

        count = 0
        while True:
            if prev_date in self.trading_days:
                count += 1
                if count == skip:
                    return prev_date
            prev_date -= timedelta(days=1)

            # 防止无限循环
            if (date_normalized - prev_date).days > 365:
                raise ValueError(f"Cannot find previous trading day before {date}")

    def get_trading_days_between(
        self,
        start_date: datetime,
        end_date: datetime,
        inclusive: bool = True
    ) -> List[datetime]:
        """
        获取日期区间内的所有交易日

        Args:
            start_date: 起始日期
            end_date: 结束日期
            inclusive: 是否包含起止日期（默认True）

        Returns:
            List[datetime]: 交易日列表（按时间顺序）
        """
        start_normalized = datetime(start_date.year, start_date.month, start_date.day)
        end_normalized = datetime(end_date.year, end_date.month, end_date.day)

        if inclusive:
            trading_days = [
                d for d in self.trading_days
                if start_normalized <= d <= end_normalized
            ]
        else:
            trading_days = [
                d for d in self.trading_days
                if start_normalized < d < end_normalized
            ]

        return sorted(trading_days)

    def count_trading_days(self, start_date: datetime, end_date: datetime) -> int:
        """
        计算日期区间内的交易日数量

        Args:
            start_date: 起始日期
            end_date: 结束日期

        Returns:
            int: 交易日数量
        """
        return len(self.get_trading_days_between(start_date, end_date))

    def get_latest_trading_day(self) -> datetime:
        """
        获取最新的交易日

        Returns:
            datetime: 最新交易日
        """
        return max(self.trading_days)

    def get_earliest_trading_day(self) -> datetime:
        """
        获取最早的交易日

        Returns:
            datetime: 最早交易日
        """
        return min(self.trading_days)

    def __repr__(self) -> str:
        return f"TradingCalendar(market={self.market}, days={len(self.trading_days)})"


# 全局单例
_calendars = {}


def get_trading_calendar(market: str = 'CN') -> TradingCalendar:
    """
    获取交易日历单例

    Args:
        market: 市场代码

    Returns:
        TradingCalendar: 交易日历实例
    """
    if market not in _calendars:
        _calendars[market] = TradingCalendar(market)
    return _calendars[market]
