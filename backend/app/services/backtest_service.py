"""Backtesting engine."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime


class BacktestService:
    """Service for backtesting trading strategies."""

    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.0003,
        min_commission: float = 5.0
    ):
        """Initialize backtest service.

        Args:
            initial_capital: Initial capital
            commission_rate: Commission rate (0.0003 = 0.03%)
            min_commission: Minimum commission per trade
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.min_commission = min_commission

    def calculate_commission(self, amount: float) -> float:
        """Calculate commission for a trade.

        Args:
            amount: Trade amount

        Returns:
            Commission amount
        """
        commission = amount * self.commission_rate
        return max(commission, self.min_commission)

    def run_backtest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run backtest on data with signals.

        Args:
            df: DataFrame with 'signal' column (1=buy, -1=sell, 0=hold)

        Returns:
            Backtest results dictionary
        """
        # Initialize
        capital = self.initial_capital
        position = 0  # Number of shares held
        cost_basis = 0  # Average cost per share
        trades = []
        equity_curve = []

        # Track daily equity
        for i in range(len(df)):
            row = df.iloc[i]
            signal = row['signal']
            price = row['close']
            date = row['date']

            # Buy signal
            if signal == 1 and position == 0:
                # Buy with all available capital
                shares_to_buy = int(capital / (price * (1 + self.commission_rate)))
                if shares_to_buy > 0:
                    trade_amount = shares_to_buy * price
                    commission = self.calculate_commission(trade_amount)
                    total_cost = trade_amount + commission

                    if total_cost <= capital:
                        position = shares_to_buy
                        cost_basis = price
                        capital -= total_cost

                        trades.append({
                            'date': date,
                            'type': 'buy',
                            'price': price,
                            'shares': shares_to_buy,
                            'amount': trade_amount,
                            'commission': commission,
                            'capital': capital
                        })

            # Sell signal
            elif signal == -1 and position > 0:
                # Sell all shares
                trade_amount = position * price
                commission = self.calculate_commission(trade_amount)
                proceeds = trade_amount - commission
                capital += proceeds

                profit = (price - cost_basis) * position - commission
                profit_pct = (price - cost_basis) / cost_basis * 100

                trades.append({
                    'date': date,
                    'type': 'sell',
                    'price': price,
                    'shares': position,
                    'amount': trade_amount,
                    'commission': commission,
                    'capital': capital,
                    'profit': profit,
                    'profit_pct': profit_pct
                })

                position = 0
                cost_basis = 0

            # Calculate current equity
            if position > 0:
                equity = capital + position * price
            else:
                equity = capital

            equity_curve.append({
                'date': date,
                'equity': equity,
                'capital': capital,
                'position_value': position * price if position > 0 else 0
            })

        # Close any open position at the end
        if position > 0:
            last_row = df.iloc[-1]
            price = last_row['close']
            date = last_row['date']
            trade_amount = position * price
            commission = self.calculate_commission(trade_amount)
            proceeds = trade_amount - commission
            capital += proceeds

            profit = (price - cost_basis) * position - commission
            profit_pct = (price - cost_basis) / cost_basis * 100

            trades.append({
                'date': date,
                'type': 'sell',
                'price': price,
                'shares': position,
                'amount': trade_amount,
                'commission': commission,
                'capital': capital,
                'profit': profit,
                'profit_pct': profit_pct
            })

            position = 0

        # Calculate statistics
        final_capital = capital
        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100

        # Calculate metrics
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit', 0) < 0]
        total_trades = len([t for t in trades if t['type'] == 'buy'])

        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0

        # Calculate max drawdown
        equity_series = pd.Series([e['equity'] for e in equity_curve])
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()

        # Average profit/loss
        avg_profit = np.mean([t.get('profit', 0) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.get('profit', 0) for t in losing_trades]) if losing_trades else 0

        # Profit factor
        total_profit = sum([t.get('profit', 0) for t in winning_trades])
        total_loss = abs(sum([t.get('profit', 0) for t in losing_trades]))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')

        return {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades': trades,
            'equity_curve': equity_curve
        }
