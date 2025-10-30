"""Stock data fetching service using AkShare."""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


class DataService:
    """Service for fetching stock market data."""

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
            symbol: Stock code (e.g., '000001', '600000')
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

            # Fetch data from AkShare
            df = ak.stock_zh_a_hist(
                symbol=symbol,
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
            stock_list = ak.stock_info_a_code_name()
            stock = stock_list[stock_list['code'] == symbol]

            if stock.empty:
                raise Exception(f"Stock {symbol} not found")

            return {
                'code': symbol,
                'name': stock.iloc[0]['name'],
                'market': 'A-share'
            }
        except Exception as e:
            raise Exception(f"Failed to fetch stock info: {str(e)}")
