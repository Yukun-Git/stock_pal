"""数据适配器基类.

定义所有数据源适配器必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class BaseDataAdapter(ABC):
    """数据源适配器抽象基类.

    所有数据源适配器都必须继承此类并实现所有抽象方法。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """适配器名称."""
        pass

    @abstractmethod
    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """获取股票历史数据.

        Args:
            symbol: 股票代码 (e.g., '000001', '600519.SH', '00700.HK')
            start_date: 开始日期 'YYYYMMDD' 格式
            end_date: 结束日期 'YYYYMMDD' 格式
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, ''=不复权)

        Returns:
            DataFrame包含以下标准列:
            - date: 日期 (datetime)
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额 (可选)
            - amplitude: 振幅 (可选)
            - pct_change: 涨跌幅 (可选)
            - change: 涨跌额 (可选)
            - turnover: 换手率 (可选)

        Raises:
            Exception: 获取数据失败时抛出异常
        """
        pass

    @abstractmethod
    def search_stock(self, keyword: str) -> list:
        """搜索股票.

        Args:
            keyword: 搜索关键词 (股票代码或名称)

        Returns:
            股票列表，每个元素是包含 code 和 name 的字典

        Raises:
            Exception: 搜索失败时抛出异常
        """
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> dict:
        """获取股票基本信息.

        Args:
            symbol: 股票代码

        Returns:
            包含股票基本信息的字典:
            - code: 股票代码
            - name: 股票名称
            - market: 市场类型 (e.g., 'A-share', 'HK', 'US')

        Raises:
            Exception: 获取失败时返回通用信息
        """
        pass

    def _detect_market(self, symbol: str) -> str:
        """检测股票市场类型.

        Args:
            symbol: 股票代码

        Returns:
            市场类型: 'A-share', 'HK', 'US', 'Unknown'
        """
        # 港股检测
        if '.HK' in symbol.upper():
            return 'HK'

        # 美股检测 (通常有点号但不是.HK/.SH/.SZ)
        if '.' in symbol and not any(x in symbol.upper() for x in ['.SH', '.SZ']):
            return 'US'

        # A股检测
        base_symbol = symbol.split('.')[0]
        if base_symbol.isdigit() and len(base_symbol) == 6:
            if base_symbol.startswith('6'):
                return 'A-share'  # 上海
            elif base_symbol.startswith(('0', '3')):
                return 'A-share'  # 深圳
            elif base_symbol.startswith('8') or base_symbol.startswith('4'):
                return 'A-share'  # 北交所

        return 'Unknown'

    def _normalize_stock_code(self, symbol: str) -> str:
        """规范化股票代码.

        移除可选的交易所后缀，返回基础代码。

        Args:
            symbol: 股票代码

        Returns:
            规范化后的代码
        """
        # 港股：移除 .HK
        if '.HK' in symbol.upper():
            return symbol.replace('.HK', '').replace('.hk', '')

        # A股：移除 .SH/.SZ
        if '.' in symbol:
            return symbol.split('.')[0]

        return symbol

    def supports_market(self, market: str) -> bool:
        """检查适配器是否支持指定市场.

        Args:
            market: 市场类型

        Returns:
            是否支持
        """
        # 默认实现，子类可以覆盖
        return True
