"""
性能指标计算器

计算回测的各项性能指标，包括：
- 收益指标：总收益、年化收益（CAGR）
- 风险指标：波动率、最大回撤
- 风险调整收益：Sharpe、Sortino、Calmar
- 交易统计：胜率、盈亏比
- 基准对比：alpha、beta、信息比率
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

from .models import Trade, OrderSide

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    性能指标计算器

    所有方法都是静态方法，可以直接调用而无需实例化。
    """

    TRADING_DAYS_PER_YEAR = 252  # 每年约252个交易日

    # ==================== 收益指标 ====================

    @staticmethod
    def total_return(equity_curve: pd.Series) -> float:
        """
        计算总收益率

        Args:
            equity_curve: 权益曲线（Series，index为日期）

        Returns:
            float: 总收益率（小数形式，如0.25表示25%）
        """
        if len(equity_curve) == 0:
            return 0.0

        initial = equity_curve.iloc[0]
        final = equity_curve.iloc[-1]

        if initial == 0:
            return 0.0

        return (final - initial) / initial

    @staticmethod
    def cagr(equity_curve: pd.Series) -> float:
        """
        计算复合年化增长率 (Compound Annual Growth Rate)

        Args:
            equity_curve: 权益曲线

        Returns:
            float: CAGR（年化收益率）
        """
        if len(equity_curve) < 2:
            return 0.0

        initial = equity_curve.iloc[0]
        final = equity_curve.iloc[-1]
        num_days = len(equity_curve)
        num_years = num_days / MetricsCalculator.TRADING_DAYS_PER_YEAR

        if initial == 0 or num_years == 0:
            return 0.0

        return (final / initial) ** (1 / num_years) - 1

    @staticmethod
    def annual_return(returns: pd.Series) -> float:
        """
        计算年化收益率（基于日收益率）

        Args:
            returns: 日收益率序列

        Returns:
            float: 年化收益率
        """
        if len(returns) == 0:
            return 0.0

        return returns.mean() * MetricsCalculator.TRADING_DAYS_PER_YEAR

    # ==================== 风险指标 ====================

    @staticmethod
    def volatility(returns: pd.Series, annualized: bool = True) -> float:
        """
        计算波动率（标准差）

        Args:
            returns: 日收益率序列
            annualized: 是否年化

        Returns:
            float: 波动率
        """
        if len(returns) < 2:
            return 0.0

        std = returns.std()

        if annualized:
            return std * np.sqrt(MetricsCalculator.TRADING_DAYS_PER_YEAR)
        else:
            return std

    @staticmethod
    def max_drawdown(equity_curve: pd.Series) -> float:
        """
        计算最大回撤

        Args:
            equity_curve: 权益曲线

        Returns:
            float: 最大回撤（负数，如-0.15表示-15%）
        """
        if len(equity_curve) == 0:
            return 0.0

        # 计算累计最大值
        rolling_max = equity_curve.expanding().max()

        # 计算回撤
        drawdown = (equity_curve - rolling_max) / rolling_max

        # 返回最大回撤（最小值）
        return drawdown.min()

    @staticmethod
    def max_drawdown_duration(equity_curve: pd.Series) -> int:
        """
        计算最大回撤持续天数

        Args:
            equity_curve: 权益曲线

        Returns:
            int: 最大回撤持续天数
        """
        if len(equity_curve) == 0:
            return 0

        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max

        # 找到回撤期（非零回撤）
        is_drawdown = drawdown < 0

        # 计算连续回撤天数
        max_duration = 0
        current_duration = 0

        for dd in is_drawdown:
            if dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_duration

    # ==================== 风险调整收益 ====================

    @staticmethod
    def sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.03
    ) -> float:
        """
        计算 Sharpe 比率

        Sharpe = (年化收益 - 无风险利率) / 年化波动率

        Args:
            returns: 日收益率序列
            risk_free_rate: 无风险利率（年化）

        Returns:
            float: Sharpe 比率
        """
        if len(returns) < 2:
            return 0.0

        # 日无风险利率
        daily_rf = risk_free_rate / MetricsCalculator.TRADING_DAYS_PER_YEAR

        # 超额收益
        excess_returns = returns - daily_rf

        std = excess_returns.std()
        if std == 0 or std < 1e-10:  # 使用阈值避免除以极小的数
            return 0.0

        # Sharpe 比率（年化）
        return np.sqrt(MetricsCalculator.TRADING_DAYS_PER_YEAR) * excess_returns.mean() / std

    @staticmethod
    def sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.03
    ) -> float:
        """
        计算 Sortino 比率

        Sortino = (年化收益 - 无风险利率) / 下行波动率

        只考虑负收益的波动率，比 Sharpe 更关注下行风险。

        Args:
            returns: 日收益率序列
            risk_free_rate: 无风险利率（年化）

        Returns:
            float: Sortino 比率
        """
        if len(returns) < 2:
            return 0.0

        daily_rf = risk_free_rate / MetricsCalculator.TRADING_DAYS_PER_YEAR
        excess_returns = returns - daily_rf

        # 只取负收益
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return 0.0

        downside_std = downside_returns.std()
        if downside_std == 0 or downside_std < 1e-10:  # 使用阈值避免除以极小的数
            return 0.0

        # Sortino 比率（年化）
        return np.sqrt(MetricsCalculator.TRADING_DAYS_PER_YEAR) * excess_returns.mean() / downside_std

    @staticmethod
    def calmar_ratio(equity_curve: pd.Series) -> float:
        """
        计算 Calmar 比率

        Calmar = 年化收益 / |最大回撤|

        衡量收益和回撤的比例，越大越好。

        Args:
            equity_curve: 权益曲线

        Returns:
            float: Calmar 比率
        """
        if len(equity_curve) < 2:
            return 0.0

        cagr_value = MetricsCalculator.cagr(equity_curve)
        max_dd = MetricsCalculator.max_drawdown(equity_curve)

        # 使用阈值避免除以极小的数
        if max_dd == 0 or abs(max_dd) < 1e-10:
            return 0.0

        return cagr_value / abs(max_dd)

    # ==================== 交易统计 ====================

    @staticmethod
    def win_rate(trades: List[Trade]) -> float:
        """
        计算胜率

        Args:
            trades: 交易记录列表

        Returns:
            float: 胜率（0-1之间）
        """
        if not trades:
            return 0.0

        # 只统计完整的买卖对
        buy_trades = [t for t in trades if t.side == OrderSide.BUY]
        sell_trades = [t for t in trades if t.side == OrderSide.SELL]

        if len(buy_trades) == 0 or len(sell_trades) == 0:
            return 0.0

        # 简化：假设买卖配对，计算盈利次数
        winning_trades = 0
        total_pairs = min(len(buy_trades), len(sell_trades))

        for i in range(total_pairs):
            buy_price = buy_trades[i].price
            sell_price = sell_trades[i].price
            if sell_price > buy_price:
                winning_trades += 1

        return winning_trades / total_pairs if total_pairs > 0 else 0.0

    @staticmethod
    def profit_factor(trades: List[Trade]) -> float:
        """
        计算盈亏比 (Profit Factor)

        盈亏比 = 总盈利 / 总亏损

        Args:
            trades: 交易记录列表

        Returns:
            float: 盈亏比
        """
        if not trades:
            return 0.0

        buy_trades = [t for t in trades if t.side == OrderSide.BUY]
        sell_trades = [t for t in trades if t.side == OrderSide.SELL]

        if len(buy_trades) == 0 or len(sell_trades) == 0:
            return 0.0

        total_profit = 0.0
        total_loss = 0.0
        total_pairs = min(len(buy_trades), len(sell_trades))

        for i in range(total_pairs):
            buy_cost = buy_trades[i].amount + buy_trades[i].commission
            sell_proceeds = sell_trades[i].amount - sell_trades[i].commission - sell_trades[i].stamp_tax
            pnl = sell_proceeds - buy_cost

            if pnl > 0:
                total_profit += pnl
            else:
                total_loss += abs(pnl)

        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0

        return total_profit / total_loss

    @staticmethod
    def avg_trade_return(trades: List[Trade]) -> float:
        """
        计算平均交易收益率

        Args:
            trades: 交易记录列表

        Returns:
            float: 平均交易收益率（小数形式，如0.05表示5%）
        """
        if not trades:
            return 0.0

        buy_trades = [t for t in trades if t.side == OrderSide.BUY]
        sell_trades = [t for t in trades if t.side == OrderSide.SELL]

        if len(buy_trades) == 0 or len(sell_trades) == 0:
            return 0.0

        returns = []
        total_pairs = min(len(buy_trades), len(sell_trades))

        for i in range(total_pairs):
            buy_cost = buy_trades[i].amount + buy_trades[i].commission
            sell_proceeds = sell_trades[i].amount - sell_trades[i].commission - sell_trades[i].stamp_tax
            trade_return = (sell_proceeds - buy_cost) / buy_cost
            returns.append(trade_return)

        return np.mean(returns) if returns else 0.0

    @staticmethod
    def avg_profit_amount(trades: List[Trade]) -> float:
        """
        计算盈利交易的平均盈利金额

        Args:
            trades: 交易记录列表

        Returns:
            float: 平均盈利金额
        """
        if not trades:
            return 0.0

        buy_trades = [t for t in trades if t.side == OrderSide.BUY]
        sell_trades = [t for t in trades if t.side == OrderSide.SELL]

        if len(buy_trades) == 0 or len(sell_trades) == 0:
            return 0.0

        profits = []
        total_pairs = min(len(buy_trades), len(sell_trades))

        for i in range(total_pairs):
            buy_cost = buy_trades[i].amount + buy_trades[i].commission
            sell_proceeds = sell_trades[i].amount - sell_trades[i].commission - sell_trades[i].stamp_tax
            pnl = sell_proceeds - buy_cost

            if pnl > 0:
                profits.append(pnl)

        return np.mean(profits) if profits else 0.0

    @staticmethod
    def avg_loss_amount(trades: List[Trade]) -> float:
        """
        计算亏损交易的平均亏损金额（绝对值）

        Args:
            trades: 交易记录列表

        Returns:
            float: 平均亏损金额（绝对值）
        """
        if not trades:
            return 0.0

        buy_trades = [t for t in trades if t.side == OrderSide.BUY]
        sell_trades = [t for t in trades if t.side == OrderSide.SELL]

        if len(buy_trades) == 0 or len(sell_trades) == 0:
            return 0.0

        losses = []
        total_pairs = min(len(buy_trades), len(sell_trades))

        for i in range(total_pairs):
            buy_cost = buy_trades[i].amount + buy_trades[i].commission
            sell_proceeds = sell_trades[i].amount - sell_trades[i].commission - sell_trades[i].stamp_tax
            pnl = sell_proceeds - buy_cost

            if pnl < 0:
                losses.append(abs(pnl))

        return np.mean(losses) if losses else 0.0

    @staticmethod
    def turnover_rate(trades: List[Trade], equity_curve: pd.Series) -> float:
        """
        计算换手率（年化）

        换手率 = (买入金额总和 + 卖出金额总和) / 2 / 平均资产 * 年化因子

        Args:
            trades: 交易记录列表
            equity_curve: 权益曲线

        Returns:
            float: 年化换手率
        """
        if not trades or len(equity_curve) == 0:
            return 0.0

        total_volume = sum([t.amount for t in trades])
        avg_equity = equity_curve.mean()
        num_years = len(equity_curve) / MetricsCalculator.TRADING_DAYS_PER_YEAR

        if avg_equity == 0 or num_years == 0:
            return 0.0

        return (total_volume / 2) / avg_equity / num_years

    @staticmethod
    def avg_holding_period(trades: List[Trade]) -> float:
        """
        计算平均持仓天数

        Args:
            trades: 交易记录列表

        Returns:
            float: 平均持仓天数
        """
        if not trades:
            return 0.0

        buy_trades = [t for t in trades if t.side == OrderSide.BUY]
        sell_trades = [t for t in trades if t.side == OrderSide.SELL]

        if len(buy_trades) == 0 or len(sell_trades) == 0:
            return 0.0

        holding_periods = []
        total_pairs = min(len(buy_trades), len(sell_trades))

        for i in range(total_pairs):
            buy_date = buy_trades[i].executed_at
            sell_date = sell_trades[i].executed_at
            holding_days = (sell_date - buy_date).days
            holding_periods.append(holding_days)

        return np.mean(holding_periods) if holding_periods else 0.0

    # ==================== 基准对比 ====================

    @staticmethod
    def alpha(
        returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free_rate: float = 0.03
    ) -> float:
        """
        计算 Alpha（超额收益）

        Alpha = 策略年化收益 - (无风险利率 + Beta * (基准年化收益 - 无风险利率))

        Args:
            returns: 策略日收益率
            benchmark_returns: 基准日收益率
            risk_free_rate: 无风险利率

        Returns:
            float: Alpha
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        strategy_annual_return = MetricsCalculator.annual_return(returns)
        benchmark_annual_return = MetricsCalculator.annual_return(benchmark_returns)
        beta_value = MetricsCalculator.beta(returns, benchmark_returns)

        return strategy_annual_return - (risk_free_rate + beta_value * (benchmark_annual_return - risk_free_rate))

    @staticmethod
    def beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        计算 Beta（系统风险）

        Beta = Cov(策略收益, 基准收益) / Var(基准收益)

        Args:
            returns: 策略日收益率
            benchmark_returns: 基准日收益率

        Returns:
            float: Beta
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        # 对齐数据
        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')

        if len(aligned_returns) < 2:
            return 0.0

        covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
        benchmark_variance = np.var(aligned_benchmark)

        if benchmark_variance == 0:
            return 0.0

        return covariance / benchmark_variance

    @staticmethod
    def information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        计算信息比率

        IR = (策略收益 - 基准收益) / 跟踪误差

        Args:
            returns: 策略日收益率
            benchmark_returns: 基准日收益率

        Returns:
            float: 信息比率
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')

        if len(aligned_returns) < 2:
            return 0.0

        excess_returns = aligned_returns - aligned_benchmark
        tracking_error = excess_returns.std()

        if tracking_error == 0:
            return 0.0

        return excess_returns.mean() / tracking_error * np.sqrt(MetricsCalculator.TRADING_DAYS_PER_YEAR)

    @staticmethod
    def tracking_error(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        计算跟踪误差（年化）

        TE = Std(策略收益 - 基准收益) * sqrt(252)

        Args:
            returns: 策略日收益率
            benchmark_returns: 基准日收益率

        Returns:
            float: 跟踪误差（年化）
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')

        if len(aligned_returns) < 2:
            return 0.0

        excess_returns = aligned_returns - aligned_benchmark
        return excess_returns.std() * np.sqrt(MetricsCalculator.TRADING_DAYS_PER_YEAR)

    # ==================== 综合计算 ====================

    @staticmethod
    def calculate_all_metrics(
        equity_curve: pd.Series,
        trades: List[Trade],
        benchmark_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.03
    ) -> Dict[str, float]:
        """
        计算所有性能指标

        Args:
            equity_curve: 权益曲线
            trades: 交易记录列表
            benchmark_returns: 基准收益率（可选）
            risk_free_rate: 无风险利率

        Returns:
            Dict[str, float]: 所有指标的字典
        """
        if len(equity_curve) == 0:
            return {}

        # 计算日收益率
        returns = equity_curve.pct_change().dropna()

        metrics = {
            # 收益指标
            'total_return': MetricsCalculator.total_return(equity_curve),
            'cagr': MetricsCalculator.cagr(equity_curve),
            'annual_return': MetricsCalculator.annual_return(returns),

            # 风险指标
            'volatility': MetricsCalculator.volatility(returns),
            'max_drawdown': MetricsCalculator.max_drawdown(equity_curve),
            'max_drawdown_duration': float(MetricsCalculator.max_drawdown_duration(equity_curve)),

            # 风险调整收益
            'sharpe_ratio': MetricsCalculator.sharpe_ratio(returns, risk_free_rate),
            'sortino_ratio': MetricsCalculator.sortino_ratio(returns, risk_free_rate),
            'calmar_ratio': MetricsCalculator.calmar_ratio(equity_curve),

            # 交易统计
            'total_trades': float(len([t for t in trades if t.side == OrderSide.BUY])),
            'win_rate': MetricsCalculator.win_rate(trades),
            'profit_factor': MetricsCalculator.profit_factor(trades),
            'avg_trade_return': MetricsCalculator.avg_trade_return(trades),
            'avg_profit_amount': MetricsCalculator.avg_profit_amount(trades),
            'avg_loss_amount': MetricsCalculator.avg_loss_amount(trades),

            # 持仓统计
            'turnover_rate': MetricsCalculator.turnover_rate(trades, equity_curve),
            'avg_holding_period': MetricsCalculator.avg_holding_period(trades),
        }

        # 基准对比（如果提供）
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            metrics.update({
                'alpha': MetricsCalculator.alpha(returns, benchmark_returns, risk_free_rate),
                'beta': MetricsCalculator.beta(returns, benchmark_returns),
                'information_ratio': MetricsCalculator.information_ratio(returns, benchmark_returns),
                'tracking_error': MetricsCalculator.tracking_error(returns, benchmark_returns),
            })

        return metrics
