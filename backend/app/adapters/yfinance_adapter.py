"""YFinance数据适配器.

基于yfinance库的数据源适配器实现。
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional

from .base import BaseDataAdapter


class YFinanceAdapter(BaseDataAdapter):
    """YFinance数据源适配器.

    提供基于Yahoo Finance的全球股票数据获取能力。
    支持A股、港股、美股等多个市场。
    """

    @property
    def name(self) -> str:
        """适配器名称."""
        return "YFinance"

    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """获取股票历史数据.

        Args:
            symbol: 股票代码
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'
            adjust: 复权类型 (yfinance默认已复权)

        Returns:
            标准格式的DataFrame

        Raises:
            Exception: 获取失败
        """
        try:
            # 转换股票代码为yfinance格式
            yf_symbol = self._convert_to_yf_symbol(symbol)

            # 转换日期格式 YYYYMMDD -> YYYY-MM-DD
            start = datetime.strptime(start_date, '%Y%m%d').strftime('%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')

            # 获取数据
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start, end=end, auto_adjust=True)

            if df.empty:
                raise Exception(f"No data found for symbol {symbol}")

            # 转换为标准格式
            df = self._normalize_dataframe(df)

            return df

        except Exception as e:
            raise Exception(f"Failed to fetch stock data: {str(e)}")

    def _convert_to_yf_symbol(self, symbol: str) -> str:
        """将股票代码转换为yfinance格式.

        Args:
            symbol: 原始股票代码

        Returns:
            yfinance格式的代码

        Examples:
            600519 -> 600519.SS
            600519.SH -> 600519.SS
            000001.SZ -> 000001.SZ
            01810.HK -> 1810.HK
            00700.HK -> 0700.HK
        """
        # 检测市场类型
        market = self._detect_market(symbol)

        if market == 'HK':
            # 港股：移除前导0（yfinance格式）
            base_code = self._normalize_stock_code(symbol)
            # 移除前导0
            base_code = base_code.lstrip('0')
            if not base_code:  # 如果全是0，保留一个
                base_code = '0'
            return f"{base_code}.HK"

        elif market == 'A-share':
            # A股：添加交易所后缀
            base_code = self._normalize_stock_code(symbol)

            # 判断交易所
            if base_code.startswith('6'):
                # 上海交易所
                return f"{base_code}.SS"
            elif base_code.startswith(('0', '3')):
                # 深圳交易所
                return f"{base_code}.SZ"
            elif base_code.startswith(('8', '4')):
                # 北京交易所
                return f"{base_code}.BJ"
            else:
                # 默认深圳
                return f"{base_code}.SZ"

        else:
            # 其他市场，保持原样
            return symbol

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """将yfinance的DataFrame转换为标准格式.

        Args:
            df: yfinance返回的DataFrame

        Returns:
            标准格式的DataFrame
        """
        # 重置索引，将日期从索引变为列
        df = df.reset_index()

        # 重命名列
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
        }

        df = df.rename(columns=column_mapping)

        # 只保留需要的列
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        df = df[required_columns]

        # 计算额外字段
        # 振幅 = (最高 - 最低) / 前收盘 * 100
        prev_close = df['close'].shift(1)
        df['amplitude'] = ((df['high'] - df['low']) / prev_close * 100).round(2)
        df.loc[0, 'amplitude'] = (
            (df.loc[0, 'high'] - df.loc[0, 'low']) / df.loc[0, 'low'] * 100
            if df.loc[0, 'low'] > 0 else 0
        )

        # 涨跌幅 = (收盘 - 前收盘) / 前收盘 * 100
        df['pct_change'] = ((df['close'] - prev_close) / prev_close * 100).round(2)
        df.loc[0, 'pct_change'] = 0

        # 涨跌额 = 收盘 - 前收盘
        df['change'] = (df['close'] - prev_close).round(2)
        df.loc[0, 'change'] = 0

        # 成交额 (yfinance不提供，设为None)
        df['amount'] = None

        # 换手率 (yfinance不提供，设为None)
        df['turnover'] = None

        # 确保日期格式正确
        df['date'] = pd.to_datetime(df['date'])

        # 移除时区信息（保持与akshare一致）
        if df['date'].dt.tz is not None:
            df['date'] = df['date'].dt.tz_localize(None)

        # 排序
        df = df.sort_values('date').reset_index(drop=True)

        return df

    def search_stock(self, keyword: str) -> list:
        """搜索股票.

        注意: yfinance不提供股票搜索功能，此方法仅返回空列表。
        建议使用其他数据源进行股票搜索。

        Args:
            keyword: 搜索关键词

        Returns:
            空列表
        """
        # yfinance没有提供搜索功能
        # 可以考虑集成其他API或返回空列表
        return []

    def get_stock_info(self, symbol: str) -> dict:
        """获取股票基本信息.

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典
        """
        try:
            yf_symbol = self._convert_to_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)

            # 尝试获取股票信息
            info = ticker.info

            # 提取基本信息
            name = info.get('longName') or info.get('shortName') or f'Stock {symbol}'
            market = self._detect_market(symbol)

            return {
                'code': symbol,
                'name': name,
                'market': market
            }

        except Exception:
            # 如果获取失败，返回通用信息
            return {
                'code': symbol,
                'name': f'Stock {symbol}',
                'market': self._detect_market(symbol)
            }

    def supports_market(self, market: str) -> bool:
        """检查是否支持指定市场.

        Args:
            market: 市场类型

        Returns:
            是否支持
        """
        # yfinance支持全球市场
        return market in ['A-share', 'HK', 'US', 'Unknown']
