"""Stock data caching service using PostgreSQL."""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.services.data_service import DataService
from app.utils.db import DatabaseManager

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching stock data in PostgreSQL."""

    def __init__(self):
        """Initialize cache service."""
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        try:
            with DatabaseManager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create stock_data table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS stock_data (
                            symbol VARCHAR(20) NOT NULL,
                            date DATE NOT NULL,
                            open REAL,
                            high REAL,
                            low REAL,
                            close REAL,
                            volume BIGINT,
                            amount REAL,
                            amplitude REAL,
                            pct_change REAL,
                            change REAL,
                            turnover REAL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (symbol, date)
                        )
                    """)

                    # Create index for faster queries
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_stock_data_symbol_date
                        ON stock_data(symbol, date)
                    """)

                    # Create sync log table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS data_sync_log (
                            symbol VARCHAR(20) PRIMARY KEY,
                            first_date DATE,
                            last_date DATE,
                            record_count INTEGER,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                conn.commit()
                logger.info("Cache database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _get_cache_info(self, symbol: str) -> Optional[dict]:
        """Get cache information for a symbol.

        Args:
            symbol: Stock code

        Returns:
            Dictionary with cache info (first_date, last_date, record_count)
        """
        try:
            result = DatabaseManager.execute_query(
                """
                SELECT first_date, last_date, record_count
                FROM data_sync_log
                WHERE symbol = %s
                """,
                (symbol,),
                fetch=True
            )

            if result and len(result) > 0:
                row = result[0]
                return {
                    'first_date': row['first_date'].strftime('%Y-%m-%d') if row['first_date'] else None,
                    'last_date': row['last_date'].strftime('%Y-%m-%d') if row['last_date'] else None,
                    'record_count': row['record_count']
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get cache info for {symbol}: {e}")
            return None

    def _update_sync_log(self, symbol: str):
        """Update sync log for a symbol.

        Args:
            symbol: Stock code
        """
        try:
            with DatabaseManager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get actual data range from stock_data table
                    cursor.execute("""
                        SELECT MIN(date), MAX(date), COUNT(*)
                        FROM stock_data
                        WHERE symbol = %s
                    """, (symbol,))

                    row = cursor.fetchone()
                    first_date, last_date, count = row

                    # Upsert sync log
                    cursor.execute("""
                        INSERT INTO data_sync_log (symbol, first_date, last_date, record_count, updated_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (symbol) DO UPDATE SET
                            first_date = EXCLUDED.first_date,
                            last_date = EXCLUDED.last_date,
                            record_count = EXCLUDED.record_count,
                            updated_at = CURRENT_TIMESTAMP
                    """, (symbol, first_date, last_date, count))

                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update sync log for {symbol}: {e}")
            raise

    def _save_to_cache(self, symbol: str, df: pd.DataFrame):
        """Save data to cache.

        Args:
            symbol: Stock code
            df: DataFrame with stock data
        """
        if df.empty:
            return

        try:
            # Prepare data for insertion
            df_copy = df.copy()
            df_copy['symbol'] = symbol

            # Convert date to string for PostgreSQL
            df_copy['date'] = pd.to_datetime(df_copy['date']).dt.strftime('%Y-%m-%d')

            # Ensure all expected columns exist (set to None if missing)
            expected_columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume',
                               'amount', 'amplitude', 'pct_change', 'change', 'turnover']
            for col in expected_columns:
                if col not in df_copy.columns:
                    df_copy[col] = None

            # Keep only expected columns in correct order
            df_copy = df_copy[expected_columns]

            # Convert to list of tuples for batch insert
            records = df_copy.to_records(index=False).tolist()

            # Batch insert with ON CONFLICT DO NOTHING (ignore duplicates)
            with DatabaseManager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany("""
                        INSERT INTO stock_data
                        (symbol, date, open, high, low, close, volume, amount,
                         amplitude, pct_change, change, turnover)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, date) DO NOTHING
                    """, records)
                conn.commit()

            # Update sync log
            self._update_sync_log(symbol)
            logger.info(f"Saved {len(records)} records to cache for {symbol}")

        except Exception as e:
            logger.error(f"Failed to save to cache for {symbol}: {e}")
            raise

    def _query_cache(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Query cached data.

        Args:
            symbol: Stock code
            start_date: Start date in 'YYYYMMDD' format
            end_date: End date in 'YYYYMMDD' format

        Returns:
            DataFrame with cached data
        """
        try:
            # Convert date format
            start = datetime.strptime(start_date, '%Y%m%d').strftime('%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')

            result = DatabaseManager.execute_query(
                """
                SELECT date, open, high, low, close, volume, amount,
                       amplitude, pct_change, change, turnover
                FROM stock_data
                WHERE symbol = %s AND date >= %s AND date <= %s
                ORDER BY date
                """,
                (symbol, start, end),
                fetch=True
            )

            if result:
                df = pd.DataFrame(result)
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to query cache for {symbol}: {e}")
            return pd.DataFrame()

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """Get stock data with caching.

        This method first checks the cache. If data is missing, it fetches
        from the data source and updates the cache.

        Args:
            symbol: Stock code (e.g., '000001', '600000')
            start_date: Start date in 'YYYYMMDD' format
            end_date: End date in 'YYYYMMDD' format
            adjust: Adjustment type ('qfq'=forward, 'hfq'=backward, ''=none)

        Returns:
            DataFrame with columns: date, open, high, low, close, volume, etc.
        """
        # Default to last 2 years if dates not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')

        # Convert to datetime for comparison
        req_start = datetime.strptime(start_date, '%Y%m%d')
        req_end = datetime.strptime(end_date, '%Y%m%d')

        # Check cache info
        cache_info = self._get_cache_info(symbol)

        need_fetch = False
        fetch_start = None
        fetch_end = None

        if cache_info is None:
            # No cache at all, fetch everything
            need_fetch = True
            fetch_start = start_date
            fetch_end = end_date
        else:
            cache_start = datetime.strptime(cache_info['first_date'], '%Y-%m-%d')
            cache_end = datetime.strptime(cache_info['last_date'], '%Y-%m-%d')

            # Check if we need data before cache range
            if req_start < cache_start:
                need_fetch = True
                fetch_start = start_date
                fetch_end = (cache_start - timedelta(days=1)).strftime('%Y%m%d')

            # Check if we need data after cache range (incremental update)
            today = datetime.now().date()
            if cache_end.date() < today and req_end > cache_end:
                need_fetch = True
                # Fetch from day after last cached date
                fetch_start = (cache_end + timedelta(days=1)).strftime('%Y%m%d')
                fetch_end = end_date

        # Fetch missing data if needed
        if need_fetch:
            try:
                logger.info(f"Fetching data for {symbol} from {fetch_start} to {fetch_end}")
                new_data = DataService.get_stock_data(
                    symbol=symbol,
                    start_date=fetch_start,
                    end_date=fetch_end,
                    adjust=adjust
                )
                if not new_data.empty:
                    self._save_to_cache(symbol, new_data)
                    logger.info(f"Saved {len(new_data)} records to cache")
            except Exception as e:
                logger.warning(f"Failed to fetch data: {str(e)}")
                # Continue with cached data if available

        # Query cache for requested range
        cached_data = self._query_cache(symbol, start_date, end_date)

        if cached_data.empty:
            raise Exception(f"No data available for {symbol} in range {start_date} to {end_date}")

        return cached_data

    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for a symbol or all symbols.

        Args:
            symbol: Stock code (None to clear all)
        """
        try:
            with DatabaseManager.get_connection() as conn:
                with conn.cursor() as cursor:
                    if symbol:
                        cursor.execute("DELETE FROM stock_data WHERE symbol = %s", (symbol,))
                        cursor.execute("DELETE FROM data_sync_log WHERE symbol = %s", (symbol,))
                        logger.info(f"Cleared cache for {symbol}")
                    else:
                        cursor.execute("DELETE FROM stock_data")
                        cursor.execute("DELETE FROM data_sync_log")
                        logger.info("Cleared all cache")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            stats = DatabaseManager.execute_query(
                """
                SELECT
                    COUNT(DISTINCT symbol) as symbol_count,
                    COUNT(*) as record_count,
                    MIN(date) as min_date,
                    MAX(date) as max_date
                FROM stock_data
                """,
                fetch=True
            )

            if stats and len(stats) > 0:
                row = stats[0]
                return {
                    'symbol_count': row['symbol_count'],
                    'record_count': row['record_count'],
                    'date_range': {
                        'start': row['min_date'].strftime('%Y-%m-%d') if row['min_date'] else None,
                        'end': row['max_date'].strftime('%Y-%m-%d') if row['max_date'] else None
                    }
                }
            else:
                return {
                    'symbol_count': 0,
                    'record_count': 0,
                    'date_range': {'start': None, 'end': None}
                }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                'symbol_count': 0,
                'record_count': 0,
                'date_range': {'start': None, 'end': None}
            }
