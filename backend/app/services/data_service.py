"""Stock data fetching service.

使用可配置的数据适配器获取股票数据。
支持多种数据源：AkShare、YFinance等。
支持故障转移机制。
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
from flask import current_app

from app.adapters import DataAdapterFactory
from app.services.failover_service import get_failover_service


class DataService:
    """股票数据服务.

    使用配置的数据适配器获取数据，支持动态切换数据源。
    """

    @staticmethod
    def _get_adapter():
        """获取当前配置的数据适配器实例.

        Returns:
            数据适配器实例

        Raises:
            ValueError: 如果配置的适配器不存在
        """
        # 从Flask配置中获取数据源名称
        adapter_name = current_app.config.get('DATA_SOURCE', 'yfinance')

        # 使用工厂创建适配器
        return DataAdapterFactory.create(adapter_name)

    @staticmethod
    def get_stock_list(market: str = 'A') -> pd.DataFrame:
        """获取股票列表.

        注意: 某些数据源可能不支持此功能。

        Args:
            market: 市场类型 ('A' for A-share)

        Returns:
            DataFrame with stock list
        """
        try:
            adapter = DataService._get_adapter()

            # 尝试搜索空字符串获取全部（仅AkShare支持）
            if adapter.name == 'AkShare':
                import akshare as ak
                return ak.stock_info_a_code_name()
            else:
                # 其他适配器返回空DataFrame
                return pd.DataFrame(columns=['code', 'name'])

        except Exception as e:
            raise Exception(f"Failed to fetch stock list: {str(e)}")

    @staticmethod
    def search_stock(keyword: str, use_failover: bool = True) -> list:
        """搜索股票.

        Args:
            keyword: 股票代码或名称关键词
            use_failover: 是否使用故障转移机制

        Returns:
            匹配的股票列表
        """
        if use_failover:
            # 使用故障转移服务
            try:
                failover_service = get_failover_service()
                results, adapter_name = failover_service.search_stock_with_failover(keyword)
                return results
            except Exception as e:
                raise Exception(f"Failed to search stocks: {str(e)}")
        else:
            # 使用传统方式(向后兼容)
            adapter = DataService._get_adapter()

            def fallback_to_akshare():
                """降级到AkShare搜索."""
                akshare_adapter = DataAdapterFactory.create('akshare')
                return akshare_adapter.search_stock(keyword)

            try:
                results = adapter.search_stock(keyword)

                # 当前适配器有返回结果或本身就是AkShare时直接返回
                if results or adapter.name.lower() == 'akshare':
                    return results

                # 否则尝试使用AkShare作为兜底，以保证中文搜索可用
                return fallback_to_akshare()

            except Exception as e:
                # 如果当前适配器不可用，尝试降级到AkShare
                if adapter.name.lower() != 'akshare':
                    try:
                        return fallback_to_akshare()
                    except Exception:
                        pass

                raise Exception(f"Failed to search stocks: {str(e)}")

    @staticmethod
    def get_stock_data(
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = 'qfq',
        use_failover: bool = True
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """获取股票历史数据.

        Args:
            symbol: 股票代码 (e.g., '000001', '600519.SH', '00700.HK')
            start_date: 开始日期 'YYYYMMDD' 格式 (可选)
            end_date: 结束日期 'YYYYMMDD' 格式 (可选)
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, ''=不复权)
            use_failover: 是否使用故障转移机制

        Returns:
            Tuple[DataFrame, str]: (数据, 使用的适配器名称)
            如果use_failover=False，返回 (DataFrame, None)
        """
        try:
            # 设置默认日期
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')

            if use_failover:
                # 使用故障转移服务
                failover_service = get_failover_service()
                df, adapter_name = failover_service.get_stock_data_with_failover(
                    symbol, start_date, end_date, adjust
                )
                return df, adapter_name
            else:
                # 使用传统方式(向后兼容)
                adapter = DataService._get_adapter()
                df = adapter.get_stock_data(symbol, start_date, end_date, adjust)
                return df, None

        except Exception as e:
            raise Exception(f"Failed to fetch stock data: {str(e)}")

    @staticmethod
    def get_stock_info(symbol: str) -> dict:
        """获取股票基本信息.

        Args:
            symbol: 股票代码

        Returns:
            包含股票信息的字典 (code, name, market)
        """
        try:
            adapter = DataService._get_adapter()
            return adapter.get_stock_info(symbol)

        except Exception as e:
            # 返回通用信息而不是抛出异常
            return {
                'code': symbol,
                'name': f'Stock {symbol}',
                'market': 'Unknown'
            }

    @staticmethod
    def resample_to_timeframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """将日线数据重采样为其他周期.

        Args:
            df: 日线数据，必须包含date, open, high, low, close, volume列
            timeframe: 时间周期
                - 'D': 日线（不做转换，直接返回）
                - 'W': 周线
                - 'M': 月线

        Returns:
            重采样后的DataFrame

        Raises:
            ValueError: 如果timeframe不支持
        """
        if timeframe == 'D':
            return df

        if timeframe not in ['W', 'M']:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: D, W, M")

        # 确保date列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])

        # 设置日期索引
        df = df.set_index('date')

        # OHLC重采样规则
        ohlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }

        # 如果有其他列（如amount等），也包含进来
        for col in df.columns:
            if col not in ohlc_dict:
                if col in ['amount']:
                    ohlc_dict[col] = 'sum'
                elif col in ['amplitude', 'pct_change', 'change', 'turnover']:
                    # 这些字段在重采样时不太有意义，忽略
                    pass

        # 执行重采样
        resampled = df.resample(timeframe).agg(ohlc_dict).dropna()

        # 重置索引，将date恢复为列
        resampled = resampled.reset_index()

        return resampled
