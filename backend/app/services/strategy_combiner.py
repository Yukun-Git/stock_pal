"""Strategy combination service for multi-strategy backtesting."""

import pandas as pd
from typing import List, Dict


class StrategyCombiner:
    """Combines signals from multiple strategies."""

    @staticmethod
    def combine_signals(
        df: pd.DataFrame,
        strategy_signals: List[str],
        combine_mode: str = 'AND',
        vote_threshold: int = 2
    ) -> pd.DataFrame:
        """Combine signals from multiple strategies.

        Args:
            df: DataFrame with signal columns from multiple strategies
            strategy_signals: List of signal column names (e.g., ['signal_ma', 'signal_macd'])
            combine_mode: How to combine signals - 'AND', 'OR', or 'VOTE'
            vote_threshold: For VOTE mode, minimum number of strategies that must agree

        Returns:
            DataFrame with combined 'signal' column
        """
        if not strategy_signals:
            raise ValueError("At least one strategy signal is required")

        # If only one strategy, just use its signal
        if len(strategy_signals) == 1:
            df['signal'] = df[strategy_signals[0]]
            return df

        # Combine multiple strategies
        if combine_mode == 'AND':
            # All strategies must agree on buy (1) or sell (-1)
            # Initialize with first strategy
            combined = df[strategy_signals[0]].copy()

            for signal_col in strategy_signals[1:]:
                # For each position:
                # - If both are 1 (buy), result is 1
                # - If both are -1 (sell), result is -1
                # - Otherwise (0 or disagreement), result is 0
                combined = combined.where(
                    (combined == df[signal_col]) & (combined != 0),
                    0
                )

            df['signal'] = combined

        elif combine_mode == 'OR':
            # Any strategy can trigger buy or sell
            # Priority: if any buy signal exists, buy; if any sell signal, sell
            buy_signals = sum([df[col] == 1 for col in strategy_signals])
            sell_signals = sum([df[col] == -1 for col in strategy_signals])

            df['signal'] = 0
            df.loc[buy_signals > 0, 'signal'] = 1
            df.loc[sell_signals > 0, 'signal'] = -1

            # If both buy and sell signals exist, prioritize sell (safer)
            df.loc[(buy_signals > 0) & (sell_signals > 0), 'signal'] = -1

        elif combine_mode == 'VOTE':
            # Count votes for buy/sell
            buy_votes = sum([df[col] == 1 for col in strategy_signals])
            sell_votes = sum([df[col] == -1 for col in strategy_signals])

            df['signal'] = 0
            df.loc[buy_votes >= vote_threshold, 'signal'] = 1
            df.loc[sell_votes >= vote_threshold, 'signal'] = -1

            # If both meet threshold, prioritize sell
            df.loc[
                (buy_votes >= vote_threshold) & (sell_votes >= vote_threshold),
                'signal'
            ] = -1

        else:
            raise ValueError(f"Invalid combine_mode: {combine_mode}. Must be 'AND', 'OR', or 'VOTE'")

        return df

    @staticmethod
    def get_strategy_signal_column(strategy_id: str) -> str:
        """Get the signal column name for a strategy.

        Args:
            strategy_id: Strategy identifier

        Returns:
            Signal column name (e.g., 'signal_ma_cross')
        """
        return f'signal_{strategy_id}'
