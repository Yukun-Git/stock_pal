"""Stock data caching service using SQLite."""

import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Optional
from app.services.data_service import DataService


class CacheService:
    """Service for caching stock data in SQLite."""

    def __init__(self, db_path: str = None):
        """Initialize cache service.

        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = os.getenv('DB_PATH', '/app/data/stock_cache.db')

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create stock_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
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
            CREATE INDEX IF NOT EXISTS idx_symbol_date
            ON stock_data(symbol, date)
        """)

        # Create sync log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_sync_log (
                symbol TEXT PRIMARY KEY,
                first_date DATE,
                last_date DATE,
                record_count INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def _get_cache_info(self, symbol: str) -> dict:
        """Get cache information for a symbol.

        Args:
            symbol: Stock code

        Returns:
            Dictionary with cache info (first_date, last_date, record_count)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT first_date, last_date, record_count
            FROM data_sync_log
            WHERE symbol = ?
        """, (symbol,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'first_date': row[0],
                'last_date': row[1],
                'record_count': row[2]
            }
        return None

    def _update_sync_log(self, symbol: str):
        """Update sync log for a symbol.

        Args:
            symbol: Stock code
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get actual data range from stock_data table
        cursor.execute("""
            SELECT MIN(date), MAX(date), COUNT(*)
            FROM stock_data
            WHERE symbol = ?
        """, (symbol,))

        row = cursor.fetchone()
        first_date, last_date, count = row

        # Upsert sync log
        cursor.execute("""
            INSERT INTO data_sync_log (symbol, first_date, last_date, record_count, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(symbol) DO UPDATE SET
                first_date = excluded.first_date,
                last_date = excluded.last_date,
                record_count = excluded.record_count,
                updated_at = CURRENT_TIMESTAMP
        """, (symbol, first_date, last_date, count))

        conn.commit()
        conn.close()

    def _save_to_cache(self, symbol: str, df: pd.DataFrame):
        """Save data to cache.

        Args:
            symbol: Stock code
            df: DataFrame with stock data
        """
        if df.empty:
            return

        conn = sqlite3.connect(self.db_path)

        # Add symbol column
        df_copy = df.copy()
        df_copy['symbol'] = symbol

        # Convert date to string for SQLite
        df_copy['date'] = df_copy['date'].dt.strftime('%Y-%m-%d')

        # Ensure all expected columns exist (set to None if missing)
        expected_columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume',
                           'amount', 'amplitude', 'pct_change', 'change', 'turnover']
        for col in expected_columns:
            if col not in df_copy.columns:
                df_copy[col] = None

        # Keep only expected columns in correct order
        df_copy = df_copy[expected_columns]

        # Save to database (replace duplicates)
        df_copy.to_sql('stock_data', conn, if_exists='append', index=False,
                       method='multi')

        conn.commit()
        conn.close()

        # Update sync log
        self._update_sync_log(symbol)

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
        conn = sqlite3.connect(self.db_path)

        # Convert date format
        start = datetime.strptime(start_date, '%Y%m%d').strftime('%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y%m%d').strftime('%Y-%m-%d')

        query = """
            SELECT date, open, high, low, close, volume, amount,
                   amplitude, pct_change, change, turnover
            FROM stock_data
            WHERE symbol = ? AND date >= ? AND date <= ?
            ORDER BY date
        """

        df = pd.read_sql_query(query, conn, params=(symbol, start, end))
        conn.close()

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])

        return df

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
                print(f"[Cache] Fetching data for {symbol} from {fetch_start} to {fetch_end}")
                new_data = DataService.get_stock_data(
                    symbol=symbol,
                    start_date=fetch_start,
                    end_date=fetch_end,
                    adjust=adjust
                )
                if not new_data.empty:
                    self._save_to_cache(symbol, new_data)
                    print(f"[Cache] Saved {len(new_data)} records to cache")
            except Exception as e:
                print(f"[Cache] Failed to fetch data: {str(e)}")
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if symbol:
            cursor.execute("DELETE FROM stock_data WHERE symbol = ?", (symbol,))
            cursor.execute("DELETE FROM data_sync_log WHERE symbol = ?", (symbol,))
        else:
            cursor.execute("DELETE FROM stock_data")
            cursor.execute("DELETE FROM data_sync_log")

        conn.commit()
        conn.close()

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM stock_data")
        symbol_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM stock_data")
        record_count = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(date), MAX(date) FROM stock_data")
        date_range = cursor.fetchone()

        conn.close()

        return {
            'symbol_count': symbol_count,
            'record_count': record_count,
            'date_range': {
                'start': date_range[0],
                'end': date_range[1]
            }
        }
