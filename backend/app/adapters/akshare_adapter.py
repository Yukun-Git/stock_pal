"""AkShare数据适配器.

基于AkShare库的数据源适配器实现。
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

from .base import BaseDataAdapter


class AkShareAdapter(BaseDataAdapter):
    """AkShare数据源适配器.

    提供基于AkShare的A股和港股数据获取能力。
    """

    @property
    def name(self) -> str:
        """适配器名称."""
        return "AkShare"

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
            adjust: 复权类型

        Returns:
            标准格式的DataFrame

        Raises:
            Exception: 获取失败
        """
        try:
            # 检测市场类型
            market = self._detect_market(symbol)

            if market == 'HK':
                return self._get_hk_stock_data(symbol, start_date, end_date)
            elif market == 'A-share':
                return self._get_a_share_data(symbol, start_date, end_date, adjust)
            else:
                raise Exception(f"Unsupported market for symbol: {symbol}")

        except Exception as e:
            raise Exception(f"Failed to fetch stock data: {str(e)}")

    def _get_a_share_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str
    ) -> pd.DataFrame:
        """获取A股数据.

        优先使用东方财富接口；当接口不可用或返回空数据时，降级到新浪接口，
        以保证系统在上游不稳定时仍可运行。
        """
        # 移除交易所后缀
        base_symbol = self._normalize_stock_code(symbol)

        # 自动调整结束日期到最近交易日
        df = None
        original_end_date = end_date
        max_retry_days = 14
        last_error = None

        for days_back in range(max_retry_days + 1):
            try:
                adjusted_end_date = (
                    datetime.strptime(original_end_date, '%Y%m%d') - timedelta(days=days_back)
                ).strftime('%Y%m%d')

                df = ak.stock_zh_a_hist(
                    symbol=base_symbol,
                    period='daily',
                    start_date=start_date,
                    end_date=adjusted_end_date,
                    adjust=adjust
                )

                if df is not None and not df.empty:
                    if days_back > 0:
                        print(f"Info: Adjusted end_date from {original_end_date} to {adjusted_end_date} (trading day)")
                    break
            except Exception as retry_error:
                last_error = retry_error
                if days_back == max_retry_days:
                    break
                continue

        if df is None or df.empty:
            # 降级到新浪接口
            try:
                df = self._get_a_share_data_fallback_sina(base_symbol, start_date, end_date)
            except Exception as fb_err:
                # 回退失败，抛出原始错误以便排查
                if last_error is not None:
                    raise last_error
                raise fb_err

        # 重命名列为标准格式
        if '日期' in df.columns:
            df = df.rename(columns={
                '日期': 'date',
                '股票代码': 'stock_code',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            })

        # 删除冗余列
        if 'stock_code' in df.columns:
            df = df.drop(columns=['stock_code'])

        # 转换日期类型
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])

        # 排序
        df = df.sort_values('date').reset_index(drop=True)

        return df

    def _get_hk_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取港股数据.

        优先使用东方财富接口；当接口不可用或返回空数据时，降级到新浪接口。
        """
        # 移除 .HK 后缀
        base_symbol = self._normalize_stock_code(symbol)

        # 自动调整结束日期到最近交易日
        df = None
        original_end_date = end_date
        max_retry_days = 14
        last_error = None

        for days_back in range(max_retry_days + 1):
            try:
                adjusted_end_date = (
                    datetime.strptime(original_end_date, '%Y%m%d') - timedelta(days=days_back)
                ).strftime('%Y%m%d')

                df = ak.stock_hk_hist(
                    symbol=base_symbol,
                    period='daily',
                    start_date=start_date,
                    end_date=adjusted_end_date,
                    adjust='qfq'
                )

                if df is not None and not df.empty:
                    if days_back > 0:
                        print(f"Info: Adjusted end_date from {original_end_date} to {adjusted_end_date} (trading day)")
                    break
            except Exception as retry_error:
                last_error = retry_error
                if days_back == max_retry_days:
                    break
                continue

        if df is None or df.empty:
            # 降级到新浪接口
            try:
                df = self._get_hk_stock_data_fallback_sina(base_symbol, start_date, end_date)
            except Exception as fb_err:
                if last_error is not None:
                    raise last_error
                raise fb_err

        # 重命名列
        if '日期' in df.columns:
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover'
            })

        # 计算振幅
        if 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
            prev_close = df['close'].shift(1)
            df['amplitude'] = ((df['high'] - df['low']) / prev_close * 100).round(2)
            df.loc[0, 'amplitude'] = (
                (df.loc[0, 'high'] - df.loc[0, 'low']) / df.loc[0, 'low'] * 100
                if df.loc[0, 'low'] > 0 else 0
            )
        else:
            df['amplitude'] = None

        # 转换日期
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])

        # 排序
        df = df.sort_values('date').reset_index(drop=True)

        return df

    # ------------------------------
    # Fallback (Sina) helpers
    # ------------------------------

    def _to_sina_symbol(self, base_symbol: str) -> str:
        """将A股基础代码转换为新浪格式（sh/sz前缀）。"""
        if base_symbol.startswith(('60', '68', '51')):
            return f'sh{base_symbol}'
        return f'sz{base_symbol}'

    def _get_a_share_data_fallback_sina(
        self,
        base_symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """使用新浪接口获取A股日线数据（降级路径）。"""
        sina_symbol = self._to_sina_symbol(base_symbol)
        df = ak.stock_zh_a_daily(symbol=sina_symbol)

        # 确保包含需要的列
        if 'date' not in df.columns:
            df = df.reset_index().rename(columns={df.index.name or 'index': 'date'})

        keep = [c for c in ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'turnover'] if c in df.columns]
        df = df[keep]

        # 转换日期并按范围裁剪
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        df = df[(df['date'] >= start) & (df['date'] <= end)].copy()
        df = df.sort_values('date').reset_index(drop=True)
        return df

    def _get_hk_stock_data_fallback_sina(
        self,
        base_symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """使用新浪接口获取港股日线数据（降级路径）。"""
        df = ak.stock_hk_daily(symbol=base_symbol)
        if 'date' not in df.columns:
            df = df.reset_index().rename(columns={df.index.name or 'index': 'date'})
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        df = df[(df['date'] >= start) & (df['date'] <= end)].copy()
        df = df.sort_values('date').reset_index(drop=True)
        return df

    def search_stock(self, keyword: str) -> list:
        """搜索股票.

        Args:
            keyword: 股票代码或名称

        Returns:
            股票列表
        """
        try:
            stock_list = ak.stock_info_a_code_name()

            # 搜索
            mask = (
                stock_list['code'].str.contains(keyword, case=False, na=False) |
                stock_list['name'].str.contains(keyword, case=False, na=False)
            )

            result = stock_list[mask].head(20)
            return result.to_dict('records')

        except Exception as e:
            raise Exception(f"Failed to search stocks: {str(e)}")

    def get_stock_info(self, symbol: str) -> dict:
        """获取股票基本信息.

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典
        """
        try:
            market = self._detect_market(symbol)

            if market == 'HK':
                return self._get_hk_stock_info(symbol)
            elif market == 'A-share':
                return self._get_a_share_info(symbol)
            else:
                return self._get_generic_info(symbol)

        except Exception:
            return self._get_generic_info(symbol)

    def _get_a_share_info(self, symbol: str) -> dict:
        """获取A股信息."""
        base_symbol = self._normalize_stock_code(symbol)
        stock_list = ak.stock_info_a_code_name()
        stock = stock_list[stock_list['code'] == base_symbol]

        if stock.empty:
            return self._get_generic_info(symbol)

        return {
            'code': symbol,
            'name': stock.iloc[0]['name'],
            'market': 'A-share'
        }

    def _get_hk_stock_info(self, symbol: str) -> dict:
        """获取港股信息."""
        base_code = self._normalize_stock_code(symbol)

        try:
            hk_spot = ak.stock_hk_spot()
            hk_stock = hk_spot[hk_spot['代码'] == base_code]

            if not hk_stock.empty:
                return {
                    'code': symbol,
                    'name': hk_stock.iloc[0]['名称'],
                    'market': 'HK'
                }
        except Exception:
            pass

        return {
            'code': symbol,
            'name': f'HK Stock {base_code}',
            'market': 'HK'
        }

    def _get_generic_info(self, symbol: str) -> dict:
        """通用股票信息."""
        return {
            'code': symbol,
            'name': f'Stock {symbol}',
            'market': 'Unknown'
        }
