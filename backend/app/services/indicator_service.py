"""Technical indicator calculation service."""

import pandas as pd
import numpy as np
from typing import Dict, Any


class IndicatorService:
    """Service for calculating technical indicators."""

    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
        """Calculate Moving Average.

        Args:
            df: DataFrame with price data
            periods: List of MA periods

        Returns:
            DataFrame with MA columns added
        """
        for period in periods:
            df[f'ma{period}'] = df['close'].rolling(window=period).mean()
        return df

    @staticmethod
    def calculate_ema(df: pd.DataFrame, periods: list = [12, 26]) -> pd.DataFrame:
        """Calculate Exponential Moving Average.

        Args:
            df: DataFrame with price data
            periods: List of EMA periods

        Returns:
            DataFrame with EMA columns added
        """
        for period in periods:
            df[f'ema{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        return df

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        """Calculate MACD indicator.

        Args:
            df: DataFrame with price data
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            DataFrame with MACD columns added
        """
        # Calculate EMAs
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        # MACD line (DIF)
        df['macd_dif'] = ema_fast - ema_slow

        # Signal line (DEA)
        df['macd_dea'] = df['macd_dif'].ewm(span=signal, adjust=False).mean()

        # MACD histogram (BAR)
        df['macd_bar'] = (df['macd_dif'] - df['macd_dea']) * 2

        return df

    @staticmethod
    def calculate_kdj(
        df: pd.DataFrame,
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> pd.DataFrame:
        """Calculate KDJ indicator.

        Args:
            df: DataFrame with price data
            n: RSV period
            m1: K period
            m2: D period

        Returns:
            DataFrame with KDJ columns added
        """
        # Calculate RSV
        low_min = df['low'].rolling(window=n, min_periods=1).min()
        high_max = df['high'].rolling(window=n, min_periods=1).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100

        # Calculate K and D
        df['kdj_k'] = rsv.ewm(com=m1-1, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=m2-1, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

        return df

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, periods: list = [6, 12, 24]) -> pd.DataFrame:
        """Calculate RSI indicator.

        Args:
            df: DataFrame with price data
            periods: List of RSI periods

        Returns:
            DataFrame with RSI columns added
        """
        for period in periods:
            # Calculate price changes
            delta = df['close'].diff()

            # Separate gains and losses
            gain = (delta.where(delta > 0, 0)).fillna(0)
            loss = (-delta.where(delta < 0, 0)).fillna(0)

            # Calculate average gain and loss
            avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
            avg_loss = loss.ewm(com=period-1, min_periods=period).mean()

            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            df[f'rsi{period}'] = 100 - (100 / (1 + rs))

        return df

    @staticmethod
    def calculate_boll(
        df: pd.DataFrame,
        period: int = 20,
        std: float = 2.0
    ) -> pd.DataFrame:
        """Calculate Bollinger Bands.

        Args:
            df: DataFrame with price data
            period: Moving average period
            std: Standard deviation multiplier

        Returns:
            DataFrame with BOLL columns added
        """
        df['boll_mid'] = df['close'].rolling(window=period).mean()
        rolling_std = df['close'].rolling(window=period).std()
        df['boll_upper'] = df['boll_mid'] + std * rolling_std
        df['boll_lower'] = df['boll_mid'] - std * rolling_std
        return df

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame, config: Dict[str, Any] = None) -> pd.DataFrame:
        """Calculate all technical indicators.

        Args:
            df: DataFrame with price data
            config: Configuration for indicators

        Returns:
            DataFrame with all indicators added
        """
        if config is None:
            config = {}

        # Make a copy to avoid modifying original
        df = df.copy()

        # Calculate indicators
        df = IndicatorService.calculate_ma(df, config.get('ma_periods', [5, 10, 20, 60]))
        df = IndicatorService.calculate_ema(df, config.get('ema_periods', [12, 26]))
        df = IndicatorService.calculate_macd(df)
        df = IndicatorService.calculate_kdj(df)
        df = IndicatorService.calculate_rsi(df)
        df = IndicatorService.calculate_boll(df)

        return df

    @staticmethod
    def detect_morning_star(df: pd.DataFrame, idx: int) -> bool:
        """Detect Morning Star pattern.

        Args:
            df: DataFrame with price data
            idx: Current index to check

        Returns:
            True if Morning Star pattern detected
        """
        if idx < 2:
            return False

        # Get three candles
        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]

        # First candle: long bearish (close < open)
        first_bearish = first['close'] < first['open']
        first_body = abs(first['close'] - first['open'])

        # Second candle: small body (star)
        second_body = abs(second['close'] - second['open'])
        second_small = second_body < first_body * 0.3

        # Third candle: long bullish (close > open)
        third_bullish = third['close'] > third['open']
        third_body = abs(third['close'] - third['open'])

        # Third candle closes into first candle's body
        penetration = third['close'] > (first['open'] + first['close']) / 2

        return (
            first_bearish and
            second_small and
            third_bullish and
            penetration and
            third_body > first_body * 0.5
        )

    @staticmethod
    def detect_evening_star(df: pd.DataFrame, idx: int) -> bool:
        """Detect Evening Star pattern.

        Args:
            df: DataFrame with price data
            idx: Current index to check

        Returns:
            True if Evening Star pattern detected
        """
        if idx < 2:
            return False

        # Get three candles
        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]

        # First candle: long bullish
        first_bullish = first['close'] > first['open']
        first_body = abs(first['close'] - first['open'])

        # Second candle: small body (star)
        second_body = abs(second['close'] - second['open'])
        second_small = second_body < first_body * 0.3

        # Third candle: long bearish
        third_bearish = third['close'] < third['open']
        third_body = abs(third['close'] - third['open'])

        # Third candle closes into first candle's body
        penetration = third['close'] < (first['open'] + first['close']) / 2

        return (
            first_bullish and
            second_small and
            third_bearish and
            penetration and
            third_body > first_body * 0.5
        )
