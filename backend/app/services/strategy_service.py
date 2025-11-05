"""Trading strategy definitions."""

import pandas as pd
from typing import Dict, Any, Callable
from app.services.indicator_service import IndicatorService


class StrategyService:
    """Service for defining and applying trading strategies."""

    # Strategy registry
    STRATEGIES = {}

    @classmethod
    def register_strategy(cls, name: str, description: str, parameters: list = None):
        """Decorator to register a strategy.

        Args:
            name: Strategy name
            description: Strategy description
            parameters: List of parameter definitions
        """
        def decorator(func: Callable):
            cls.STRATEGIES[name] = {
                'name': name,
                'description': description,
                'function': func,
                'parameters': parameters or []
            }
            return func
        return decorator

    @classmethod
    def get_all_strategies(cls) -> list:
        """Get all registered strategies.

        Returns:
            List of strategy metadata with parameters
        """
        return [
            {
                'id': key,
                'name': value['name'],
                'description': value['description'],
                'parameters': value.get('parameters', [])
            }
            for key, value in cls.STRATEGIES.items()
        ]

    @classmethod
    def apply_strategy(cls, strategy_id: str, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Apply a strategy to generate buy/sell signals.

        Args:
            strategy_id: Strategy ID
            df: DataFrame with price and indicator data
            params: Strategy parameters

        Returns:
            DataFrame with 'signal' column added (1=buy, -1=sell, 0=hold)
        """
        if strategy_id not in cls.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy_id}")

        strategy_func = cls.STRATEGIES[strategy_id]['function']
        return strategy_func(df, params or {})


# Define strategies using decorator

@StrategyService.register_strategy(
    name='morning_star',
    description='早晨之星：底部反转形态，三根K线组合，看涨信号',
    parameters=[
        {
            'name': 'hold_days',
            'label': '持有天数',
            'type': 'integer',
            'default': 5,
            'min': 1,
            'max': 30,
            'description': '买入后持有的天数'
        }
    ]
)
def morning_star_strategy(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Morning Star pattern strategy."""
    df = df.copy()
    df['signal'] = 0

    for i in range(2, len(df)):
        if IndicatorService.detect_morning_star(df, i):
            df.loc[i, 'signal'] = 1  # Buy signal

    # Simple exit: hold for N days or exit on evening star
    hold_days = params.get('hold_days', 5)
    for i in range(len(df)):
        if df.iloc[i]['signal'] == 1:
            # Set sell signal after hold_days
            sell_idx = min(i + hold_days, len(df) - 1)
            df.loc[sell_idx, 'signal'] = -1

        # Or exit on evening star
        if IndicatorService.detect_evening_star(df, i):
            df.loc[i, 'signal'] = -1

    return df


@StrategyService.register_strategy(
    name='ma_cross',
    description='均线金叉：短期均线上穿长期均线买入，下穿卖出',
    parameters=[
        {
            'name': 'fast_period',
            'label': '快速周期',
            'type': 'integer',
            'default': 5,
            'min': 2,
            'max': 60,
            'description': '短期移动平均线的周期'
        },
        {
            'name': 'slow_period',
            'label': '慢速周期',
            'type': 'integer',
            'default': 20,
            'min': 5,
            'max': 250,
            'description': '长期移动平均线的周期'
        }
    ]
)
def ma_cross_strategy(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Moving Average crossover strategy."""
    df = df.copy()
    df['signal'] = 0

    fast_period = params.get('fast_period', 5)
    slow_period = params.get('slow_period', 20)

    # Ensure MA columns exist
    if f'ma{fast_period}' not in df.columns:
        df = IndicatorService.calculate_ma(df, [fast_period, slow_period])

    # Generate signals
    for i in range(1, len(df)):
        fast_prev = df.iloc[i-1][f'ma{fast_period}']
        slow_prev = df.iloc[i-1][f'ma{slow_period}']
        fast_curr = df.iloc[i][f'ma{fast_period}']
        slow_curr = df.iloc[i][f'ma{slow_period}']

        # Golden cross: buy signal
        if fast_prev <= slow_prev and fast_curr > slow_curr:
            df.loc[i, 'signal'] = 1

        # Death cross: sell signal
        elif fast_prev >= slow_prev and fast_curr < slow_curr:
            df.loc[i, 'signal'] = -1

    return df


@StrategyService.register_strategy(
    name='macd_cross',
    description='MACD金叉：DIF上穿DEA买入，下穿卖出'
)
def macd_cross_strategy(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """MACD crossover strategy."""
    df = df.copy()
    df['signal'] = 0

    # Ensure MACD columns exist
    if 'macd_dif' not in df.columns:
        df = IndicatorService.calculate_macd(df)

    # Generate signals
    for i in range(1, len(df)):
        dif_prev = df.iloc[i-1]['macd_dif']
        dea_prev = df.iloc[i-1]['macd_dea']
        dif_curr = df.iloc[i]['macd_dif']
        dea_curr = df.iloc[i]['macd_dea']

        # MACD golden cross: buy signal
        if dif_prev <= dea_prev and dif_curr > dea_curr:
            df.loc[i, 'signal'] = 1

        # MACD death cross: sell signal
        elif dif_prev >= dea_prev and dif_curr < dea_curr:
            df.loc[i, 'signal'] = -1

    return df


@StrategyService.register_strategy(
    name='kdj_cross',
    description='KDJ金叉：K线上穿D线且在低位(< 30)买入，高位(> 70)卖出',
    parameters=[
        {
            'name': 'oversold',
            'label': '超卖阈值',
            'type': 'integer',
            'default': 30,
            'min': 10,
            'max': 40,
            'description': 'KDJ低于此值视为超卖区域'
        },
        {
            'name': 'overbought',
            'label': '超买阈值',
            'type': 'integer',
            'default': 70,
            'min': 60,
            'max': 90,
            'description': 'KDJ高于此值视为超买区域'
        }
    ]
)
def kdj_cross_strategy(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """KDJ crossover strategy."""
    df = df.copy()
    df['signal'] = 0

    oversold = params.get('oversold', 30)
    overbought = params.get('overbought', 70)

    # Ensure KDJ columns exist
    if 'kdj_k' not in df.columns:
        df = IndicatorService.calculate_kdj(df)

    # Generate signals
    for i in range(1, len(df)):
        k_prev = df.iloc[i-1]['kdj_k']
        d_prev = df.iloc[i-1]['kdj_d']
        k_curr = df.iloc[i]['kdj_k']
        d_curr = df.iloc[i]['kdj_d']

        # KDJ golden cross in oversold area: buy signal
        if k_prev <= d_prev and k_curr > d_curr and k_curr < oversold:
            df.loc[i, 'signal'] = 1

        # KDJ in overbought area: sell signal
        elif k_curr > overbought:
            df.loc[i, 'signal'] = -1

    return df


@StrategyService.register_strategy(
    name='rsi_reversal',
    description='RSI反转：RSI < 30超卖买入，RSI > 70超买卖出',
    parameters=[
        {
            'name': 'period',
            'label': 'RSI周期',
            'type': 'integer',
            'default': 6,
            'min': 2,
            'max': 30,
            'description': 'RSI指标的计算周期'
        },
        {
            'name': 'oversold',
            'label': '超卖阈值',
            'type': 'integer',
            'default': 30,
            'min': 10,
            'max': 40,
            'description': 'RSI低于此值视为超卖'
        },
        {
            'name': 'overbought',
            'label': '超买阈值',
            'type': 'integer',
            'default': 70,
            'min': 60,
            'max': 90,
            'description': 'RSI高于此值视为超买'
        }
    ]
)
def rsi_reversal_strategy(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """RSI reversal strategy."""
    df = df.copy()
    df['signal'] = 0

    period = params.get('period', 6)
    oversold = params.get('oversold', 30)
    overbought = params.get('overbought', 70)

    # Ensure RSI column exists
    if f'rsi{period}' not in df.columns:
        df = IndicatorService.calculate_rsi(df, [period])

    rsi_col = f'rsi{period}'

    # Generate signals
    for i in range(1, len(df)):
        rsi_prev = df.iloc[i-1][rsi_col]
        rsi_curr = df.iloc[i][rsi_col]

        # RSI crosses above oversold: buy signal
        if rsi_prev < oversold and rsi_curr >= oversold:
            df.loc[i, 'signal'] = 1

        # RSI crosses below overbought: sell signal
        elif rsi_prev > overbought and rsi_curr <= overbought:
            df.loc[i, 'signal'] = -1

    return df


@StrategyService.register_strategy(
    name='boll_breakout',
    description='布林带突破：价格突破下轨买入，突破上轨卖出'
)
def boll_breakout_strategy(df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Bollinger Bands breakout strategy."""
    df = df.copy()
    df['signal'] = 0

    # Ensure BOLL columns exist
    if 'boll_mid' not in df.columns:
        df = IndicatorService.calculate_boll(df)

    # Generate signals
    for i in range(1, len(df)):
        close_prev = df.iloc[i-1]['close']
        close_curr = df.iloc[i]['close']
        lower_prev = df.iloc[i-1]['boll_lower']
        upper_prev = df.iloc[i-1]['boll_upper']
        lower_curr = df.iloc[i]['boll_lower']
        upper_curr = df.iloc[i]['boll_upper']

        # Price breaks below lower band: buy signal (oversold)
        if close_prev > lower_prev and close_curr <= lower_curr:
            df.loc[i, 'signal'] = 1

        # Price breaks above upper band: sell signal (overbought)
        elif close_prev < upper_prev and close_curr >= upper_curr:
            df.loc[i, 'signal'] = -1

    return df
