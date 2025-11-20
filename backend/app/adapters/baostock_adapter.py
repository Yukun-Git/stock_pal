"""Baostock数据适配器.

使用Baostock API获取A股市场数据。
官网: http://baostock.com
"""

import pandas as pd
import baostock as bs
from typing import List, Dict
from datetime import datetime

from .base import BaseDataAdapter
from .exceptions import (
    NetworkException,
    TimeoutException,
    DataNotFoundException,
    DataFormatException,
    UnsupportedMarketException
)


class BaostockAdapter(BaseDataAdapter):
    """Baostock数据源适配器.

    特点：
    - 支持A股市场
    - 无需认证，免费使用
    - 稳定性好，响应速度快
    - 数据质量可靠
    """

    def __init__(self):
        """初始化适配器."""
        self._logged_in = False

    @property
    def name(self) -> str:
        """适配器名称."""
        return "baostock"

    @property
    def display_name(self) -> str:
        """适配器显示名称."""
        return "证券宝 (Baostock)"

    @property
    def supported_markets(self) -> List[str]:
        """支持的市场类型."""
        return ["A-share"]

    @property
    def requires_auth(self) -> bool:
        """是否需要认证."""
        return False

    @property
    def timeout(self) -> int:
        """请求超时时间."""
        return 10

    def _login(self):
        """登录Baostock.

        Baostock需要先登录才能使用。
        """
        if not self._logged_in:
            lg = bs.login()
            if lg.error_code != '0':
                raise NetworkException(
                    f"Baostock login failed: {lg.error_msg}",
                    adapter_name=self.name
                )
            self._logged_in = True

    def _logout(self):
        """登出Baostock."""
        if self._logged_in:
            bs.logout()
            self._logged_in = False

    def _convert_symbol_format(self, symbol: str, market: str = None) -> str:
        """转换股票代码格式为Baostock要求的格式.

        Args:
            symbol: 原始股票代码 (如 '000001', '600519')
            market: 市场类型（可选，用于判断交易所）

        Returns:
            Baostock格式代码 (如 'sz.000001', 'sh.600519')
        """
        # 移除可能的后缀
        base_symbol = self._normalize_stock_code(symbol)

        # 判断交易所
        if base_symbol.startswith('6'):
            return f'sh.{base_symbol}'  # 上海
        elif base_symbol.startswith(('0', '3')):
            return f'sz.{base_symbol}'  # 深圳
        elif base_symbol.startswith(('8', '4')):
            return f'bj.{base_symbol}'  # 北京（北交所）
        else:
            # 默认深圳
            return f'sz.{base_symbol}'

    def _convert_date_format(self, date_str: str) -> str:
        """转换日期格式.

        Args:
            date_str: YYYYMMDD格式日期

        Returns:
            YYYY-MM-DD格式日期 (Baostock要求)
        """
        if len(date_str) == 8 and date_str.isdigit():
            return f'{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}'
        return date_str

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化DataFrame格式.

        将Baostock返回的数据转换为标准格式。

        Args:
            df: Baostock原始DataFrame

        Returns:
            标准化后的DataFrame
        """
        if df is None or len(df) == 0:
            return pd.DataFrame()

        # Baostock列名映射到标准列名
        column_mapping = {
            'date': 'date',
            'code': 'symbol',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'amount': 'amount',
            'pctChg': 'pct_change',
            'turn': 'turnover'
        }

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保有date列
        if 'date' not in df.columns:
            raise DataFormatException(
                "Missing 'date' column in data",
                adapter_name=self.name
            )

        # 转换日期为datetime类型
        df['date'] = pd.to_datetime(df['date'])

        # 转换数值列为float类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 设置日期为索引
        df = df.set_index('date')

        # 按日期升序排序
        df = df.sort_index()

        # 移除NaN行
        df = df.dropna(subset=['close'])

        return df

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
            start_date: 开始日期 (YYYYMMDD格式)
            end_date: 结束日期 (YYYYMMDD格式)
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, ''=不复权)

        Returns:
            标准化的DataFrame

        Raises:
            UnsupportedMarketException: 不支持的市场
            NetworkException: 网络错误
            DataNotFoundException: 数据未找到
            DataFormatException: 数据格式错误
        """
        # 检查市场支持
        market = self._detect_market(symbol)
        if market not in self.supported_markets:
            raise UnsupportedMarketException(
                f"Market {market} not supported by Baostock",
                market=market,
                adapter_name=self.name
            )

        try:
            # 登录
            self._login()

            # 转换代码格式
            bs_symbol = self._convert_symbol_format(symbol, market)

            # 转换日期格式
            bs_start_date = self._convert_date_format(start_date)
            bs_end_date = self._convert_date_format(end_date)

            # 映射复权类型
            # Baostock: '3'=后复权, '2'=前复权, '1'=不复权
            adjust_map = {
                'qfq': '2',  # 前复权
                'hfq': '3',  # 后复权
                '': '1'      # 不复权
            }
            adjustflag = adjust_map.get(adjust, '2')

            # 请求数据
            rs = bs.query_history_k_data_plus(
                bs_symbol,
                "date,code,open,high,low,close,volume,amount,pctChg,turn",
                start_date=bs_start_date,
                end_date=bs_end_date,
                frequency="d",
                adjustflag=adjustflag
            )

            if rs is None or rs.error_code != '0':
                error_msg = rs.error_msg if rs else "Unknown error"
                raise NetworkException(
                    f"Failed to fetch data: {error_msg}",
                    adapter_name=self.name
                )

            # 提取数据
            data_list = []
            while rs.error_code == '0' and rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                raise DataNotFoundException(
                    f"No data found for symbol {symbol}",
                    adapter_name=self.name
                )

            # 转换为DataFrame
            df = pd.DataFrame(data_list, columns=rs.fields)

            # 标准化数据
            df = self._standardize_dataframe(df)

            return df

        except (UnsupportedMarketException, NetworkException, DataNotFoundException, DataFormatException):
            raise
        except Exception as e:
            raise NetworkException(
                f"Unexpected error: {str(e)}",
                adapter_name=self.name,
                original_error=e
            )
        finally:
            # 不登出，保持连接以提高性能
            pass

    def search_stock(self, keyword: str) -> list:
        """搜索股票.

        Args:
            keyword: 搜索关键词 (股票代码或名称)

        Returns:
            股票列表，格式: [{'code': str, 'name': str, 'market': str}, ...]

        Raises:
            NetworkException: 网络错误
        """
        try:
            # 登录
            self._login()

            # 获取所有股票列表
            rs = bs.query_stock_basic()

            if rs is None or rs.error_code != '0':
                error_msg = rs.error_msg if rs else "Unknown error"
                raise NetworkException(
                    f"Failed to fetch stock list: {error_msg}",
                    adapter_name=self.name
                )

            # 提取股票列表
            stock_list = []
            while rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                # row格式: [code, code_name, ipoDate, outDate, type, status]
                stock_list.append({
                    'code': row[0],  # 带前缀的代码 (如 sz.000001)
                    'name': row[1],  # 股票名称
                    'type': row[4],  # 股票类型 (1:股票, 2:指数)
                    'status': row[5]  # 状态 (1:上市, 0:退市)
                })

            # 过滤：只保留上市的股票（非指数）
            stock_list = [s for s in stock_list if s['status'] == '1' and s['type'] == '1']

            # 搜索匹配
            keyword_lower = keyword.lower()
            results = []

            for stock in stock_list:
                code = stock['code']
                name = stock['name']

                # 移除代码前缀用于匹配
                base_code = code.split('.')[-1]

                # 匹配代码或名称
                if keyword_lower in base_code.lower() or keyword_lower in name.lower():
                    results.append({
                        'code': base_code,  # 返回不带前缀的代码
                        'name': name,
                        'market': 'A-share'
                    })

            return results

        except NetworkException:
            raise
        except Exception as e:
            raise NetworkException(
                f"Unexpected error during search: {str(e)}",
                adapter_name=self.name,
                original_error=e
            )

    def get_stock_info(self, symbol: str) -> dict:
        """获取股票基本信息.

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典

        Raises:
            NetworkException: 网络错误
        """
        try:
            # 登录
            self._login()

            # 转换代码格式
            market = self._detect_market(symbol)
            bs_symbol = self._convert_symbol_format(symbol, market)

            # 获取股票列表并查找
            rs = bs.query_stock_basic()

            if rs is None or rs.error_code != '0':
                # 如果获取失败，返回基本信息
                return {
                    'code': symbol,
                    'name': 'Unknown',
                    'market': market
                }

            # 查找匹配的股票
            while rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                if row[0] == bs_symbol:
                    return {
                        'code': symbol,
                        'name': row[1],
                        'market': market,
                        'ipo_date': row[2],
                        'status': 'listed' if row[5] == '1' else 'delisted'
                    }

            # 未找到，返回默认信息
            return {
                'code': symbol,
                'name': 'Unknown',
                'market': market
            }

        except Exception as e:
            # 获取信息失败不抛异常，返回基本信息
            return {
                'code': symbol,
                'name': 'Unknown',
                'market': self._detect_market(symbol)
            }

    def __del__(self):
        """析构函数，确保登出."""
        self._logout()
