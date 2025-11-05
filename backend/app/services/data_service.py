"""Stock data fetching service using AkShare."""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


class DataService:
    """Service for fetching stock market data."""

    @staticmethod
    def _get_hk_stock_data(
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Get historical K-line data for Hong Kong stocks.

        Args:
            symbol: HK stock code (e.g., '00700.HK')
            start_date: Start date in 'YYYYMMDD' format
            end_date: End date in 'YYYYMMDD' format

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            # Remove .HK suffix and format for AkShare
            base_symbol = symbol.replace('.HK', '')

            # Convert date format from YYYYMMDD to YYYY-MM-DD
            start = datetime.strptime(start_date, '%Y%m%d').strftime('%Y%m%d')
            end = datetime.strptime(end_date, '%Y%m%d').strftime('%Y%m%d')

            # Fetch HK stock data from AkShare
            df = ak.stock_hk_hist(
                symbol=base_symbol,
                period='daily',
                start_date=start,
                end_date=end,
                adjust='qfq'
            )

            if df.empty:
                raise Exception(f"No data found for HK stock {symbol}")

            # Rename columns to match A-share format
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

            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])

            # Sort by date
            df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            raise Exception(f"Failed to fetch HK stock data: {str(e)}")

    @staticmethod
    def get_stock_list(market: str = 'A') -> pd.DataFrame:
        """Get list of stocks.

        Args:
            market: Market type ('A' for A-share)

        Returns:
            DataFrame with stock list
        """
        try:
            # Get A-share stock list
            stock_list = ak.stock_info_a_code_name()
            return stock_list
        except Exception as e:
            raise Exception(f"Failed to fetch stock list: {str(e)}")

    @staticmethod
    def search_stock(keyword: str) -> list:
        """Search stocks by code or name.

        Args:
            keyword: Stock code or name keyword

        Returns:
            List of matching stocks
        """
        try:
            stock_list = ak.stock_info_a_code_name()
            # Search by code or name
            mask = (
                stock_list['code'].str.contains(keyword, case=False, na=False) |
                stock_list['name'].str.contains(keyword, case=False, na=False)
            )
            result = stock_list[mask].head(20)  # Limit to 20 results
            return result.to_dict('records')
        except Exception as e:
            raise Exception(f"Failed to search stocks: {str(e)}")

    @staticmethod
    def get_stock_data(
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """Get historical K-line data for a stock.

        Args:
            symbol: Stock code (e.g., '000001', '600000', '600519.SH', '00700.HK')
            start_date: Start date in 'YYYYMMDD' format
            end_date: End date in 'YYYYMMDD' format
            adjust: Adjustment type ('qfq'=forward, 'hfq'=backward, ''=none)

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            # Default to last 2 years if dates not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')

            # Handle HK stocks
            if '.HK' in symbol:
                return DataService._get_hk_stock_data(symbol, start_date, end_date)

            # Handle A-share stocks
            # Remove exchange suffix for AkShare API (.SH, .SZ)
            base_symbol = symbol.split('.')[0]

            # Fetch data from AkShare
            df = ak.stock_zh_a_hist(
                symbol=base_symbol,
                period='daily',
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            if df.empty:
                raise Exception(f"No data found for stock {symbol}")

            # Rename columns to English
            df = df.rename(columns={
                '日期': 'date',
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

            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])

            # Sort by date
            df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            raise Exception(f"Failed to fetch stock data: {str(e)}")

    @staticmethod
    def get_stock_info(symbol: str) -> dict:
        """Get basic information about a stock.

        Args:
            symbol: Stock code

        Returns:
            Dictionary with stock information
        """
        try:
            # Handle HK stocks
            if '.HK' in symbol:
                base_code = symbol.split('.')[0]
                try:
                    # Try to fetch HK stock name from AkShare
                    hk_spot = ak.stock_hk_spot()
                    hk_stock = hk_spot[hk_spot['代码'] == base_code]
                    if not hk_stock.empty:
                        return {
                            'code': symbol,
                            'name': hk_stock.iloc[0]['名称'],
                            'market': 'HK'
                        }
                except:
                    pass

                # Fallback for HK stocks
                return {
                    'code': symbol,
                    'name': f'HK Stock {base_code}',
                    'market': 'HK'
                }

            # Handle A-share stocks
            # Remove exchange suffix (.SH, .SZ) for AkShare query
            base_symbol = symbol.split('.')[0]

            stock_list = ak.stock_info_a_code_name()
            stock = stock_list[stock_list['code'] == base_symbol]

            if stock.empty:
                # Return generic info if not found
                return {
                    'code': symbol,
                    'name': f'Stock {symbol}',
                    'market': 'A-share'
                }

            return {
                'code': symbol,
                'name': stock.iloc[0]['name'],
                'market': 'A-share'
            }
        except Exception as e:
            # Return generic info on error instead of raising exception
            return {
                'code': symbol,
                'name': f'Stock {symbol}',
                'market': 'Unknown'
            }
