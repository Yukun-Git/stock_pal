"""
测试性能指标计算器

测试 metrics.py 的所有功能
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.backtest.metrics import MetricsCalculator
from app.backtest.models import Trade, OrderSide


class TestMetricsCalculator:
    """测试性能指标计算器"""

    @pytest.fixture
    def sample_equity_curve(self):
        """示例权益曲线（盈利）"""
        dates = pd.date_range('2024-01-01', periods=252, freq='B')  # 一年交易日
        # 模拟盈利曲线：从100000增长到120000
        equity = np.linspace(100000, 120000, 252)
        return pd.Series(equity, index=dates)

    @pytest.fixture
    def sample_equity_curve_with_drawdown(self):
        """示例权益曲线（有回撤）"""
        dates = pd.date_range('2024-01-01', periods=100, freq='B')
        equity = [100000] * 20 + [90000] * 30 + [110000] * 50  # 回撤后上涨
        return pd.Series(equity, index=dates)

    @pytest.fixture
    def sample_trades(self):
        """示例交易记录"""
        trades = [
            # 第1笔：盈利
            Trade(
                trade_id='T1', order_id='O1', symbol='600000', side=OrderSide.BUY,
                quantity=1000, price=10.0, amount=10000, commission=5, stamp_tax=0,
                executed_at=datetime(2024, 1, 10)
            ),
            Trade(
                trade_id='T2', order_id='O2', symbol='600000', side=OrderSide.SELL,
                quantity=1000, price=11.0, amount=11000, commission=5, stamp_tax=11,
                executed_at=datetime(2024, 1, 20)
            ),
            # 第2笔：亏损
            Trade(
                trade_id='T3', order_id='O3', symbol='600000', side=OrderSide.BUY,
                quantity=1000, price=12.0, amount=12000, commission=5, stamp_tax=0,
                executed_at=datetime(2024, 2, 1)
            ),
            Trade(
                trade_id='T4', order_id='O4', symbol='600000', side=OrderSide.SELL,
                quantity=1000, price=11.5, amount=11500, commission=5, stamp_tax=11.5,
                executed_at=datetime(2024, 2, 10)
            ),
        ]
        return trades

    # ==================== 收益指标测试 ====================

    def test_total_return(self, sample_equity_curve):
        """测试总收益率"""
        total_ret = MetricsCalculator.total_return(sample_equity_curve)
        # (120000 - 100000) / 100000 = 0.20
        assert total_ret == pytest.approx(0.20, abs=0.01)

    def test_total_return_empty(self):
        """测试空权益曲线"""
        empty_curve = pd.Series([])
        assert MetricsCalculator.total_return(empty_curve) == 0.0

    def test_cagr(self, sample_equity_curve):
        """测试年化收益率（CAGR）"""
        cagr = MetricsCalculator.cagr(sample_equity_curve)
        # 一年252个交易日，从100000到120000，CAGR约20%
        assert cagr == pytest.approx(0.20, abs=0.01)

    def test_annual_return(self, sample_equity_curve):
        """测试年化收益率"""
        returns = sample_equity_curve.pct_change().dropna()
        annual_ret = MetricsCalculator.annual_return(returns)
        # 应该接近CAGR
        assert annual_ret > 0

    # ==================== 风险指标测试 ====================

    def test_volatility(self, sample_equity_curve):
        """测试波动率"""
        returns = sample_equity_curve.pct_change().dropna()
        vol = MetricsCalculator.volatility(returns, annualized=True)
        # 应该是正数
        assert vol > 0

    def test_max_drawdown(self, sample_equity_curve_with_drawdown):
        """测试最大回撤"""
        max_dd = MetricsCalculator.max_drawdown(sample_equity_curve_with_drawdown)
        # 从100000跌到90000，回撤-10%
        assert max_dd == pytest.approx(-0.10, abs=0.01)

    def test_max_drawdown_duration(self, sample_equity_curve_with_drawdown):
        """测试最大回撤持续期"""
        duration = MetricsCalculator.max_drawdown_duration(sample_equity_curve_with_drawdown)
        # 应该有回撤期
        assert duration > 0

    # ==================== 风险调整收益测试 ====================

    def test_sharpe_ratio(self, sample_equity_curve):
        """测试Sharpe比率"""
        returns = sample_equity_curve.pct_change().dropna()
        sharpe = MetricsCalculator.sharpe_ratio(returns, risk_free_rate=0.03)
        # 应该是正数（盈利且波动小）
        assert sharpe > 0

    def test_sortino_ratio(self, sample_equity_curve):
        """测试Sortino比率"""
        returns = sample_equity_curve.pct_change().dropna()
        sortino = MetricsCalculator.sortino_ratio(returns, risk_free_rate=0.03)
        # Sortino比率可能为0（如果没有负收益）或正数
        assert sortino >= 0

    def test_calmar_ratio(self, sample_equity_curve_with_drawdown):
        """测试Calmar比率"""
        calmar = MetricsCalculator.calmar_ratio(sample_equity_curve_with_drawdown)
        # Calmar = CAGR / |最大回撤|
        # 应该是正数
        assert calmar > 0

    # ==================== 交易统计测试 ====================

    def test_win_rate(self, sample_trades):
        """测试胜率"""
        win_rate = MetricsCalculator.win_rate(sample_trades)
        # 2笔交易，1盈1亏，胜率50%
        assert win_rate == pytest.approx(0.5, abs=0.1)

    def test_profit_factor(self, sample_trades):
        """测试盈亏比"""
        pf = MetricsCalculator.profit_factor(sample_trades)
        # 应该大于0
        assert pf > 0

    def test_avg_trade_return(self, sample_trades):
        """测试平均交易收益率"""
        avg_ret = MetricsCalculator.avg_trade_return(sample_trades)
        # 1盈1亏，平均应该接近0或小幅盈利
        assert isinstance(avg_ret, float)

    def test_turnover_rate(self, sample_trades, sample_equity_curve):
        """测试换手率"""
        turnover = MetricsCalculator.turnover_rate(sample_trades, sample_equity_curve)
        # 应该是正数
        assert turnover > 0

    def test_avg_holding_period(self, sample_trades):
        """测试平均持仓天数"""
        avg_period = MetricsCalculator.avg_holding_period(sample_trades)
        # 第1笔持有10天，第2笔持有9天
        assert avg_period > 0

    # ==================== 基准对比测试 ====================

    def test_beta(self, sample_equity_curve):
        """测试Beta"""
        returns = sample_equity_curve.pct_change().dropna()

        # 创建模拟基准（相关性高）
        benchmark_returns = returns * 0.9 + pd.Series(
            np.random.randn(len(returns)) * 0.00001,  # 极小的噪声
            index=returns.index
        )

        beta = MetricsCalculator.beta(returns, benchmark_returns)
        # 应该接近0.9（高度相关）
        assert 0.5 < beta < 1.5

    def test_alpha(self, sample_equity_curve):
        """测试Alpha"""
        returns = sample_equity_curve.pct_change().dropna()

        # 创建表现较差的基准
        benchmark_returns = returns * 0.5

        alpha = MetricsCalculator.alpha(returns, benchmark_returns, risk_free_rate=0.03)
        # 策略表现好于基准，alpha应该为正
        assert alpha > 0

    def test_information_ratio(self, sample_equity_curve):
        """测试信息比率"""
        returns = sample_equity_curve.pct_change().dropna()
        benchmark_returns = returns * 0.8

        ir = MetricsCalculator.information_ratio(returns, benchmark_returns)
        # 应该是有效的数字
        assert isinstance(ir, float)

    def test_tracking_error(self, sample_equity_curve):
        """测试跟踪误差"""
        returns = sample_equity_curve.pct_change().dropna()
        benchmark_returns = returns * 0.9

        te = MetricsCalculator.tracking_error(returns, benchmark_returns)
        # 应该是正数
        assert te > 0

    # ==================== 综合测试 ====================

    def test_calculate_all_metrics(self, sample_equity_curve, sample_trades):
        """测试计算所有指标"""
        metrics = MetricsCalculator.calculate_all_metrics(
            equity_curve=sample_equity_curve,
            trades=sample_trades,
            benchmark_returns=None,
            risk_free_rate=0.03
        )

        # 验证所有关键指标都存在
        assert 'total_return' in metrics
        assert 'cagr' in metrics
        assert 'volatility' in metrics
        assert 'max_drawdown' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'sortino_ratio' in metrics
        assert 'calmar_ratio' in metrics
        assert 'win_rate' in metrics
        assert 'profit_factor' in metrics
        assert 'total_trades' in metrics

    def test_calculate_all_metrics_with_benchmark(self, sample_equity_curve, sample_trades):
        """测试计算所有指标（含基准）"""
        returns = sample_equity_curve.pct_change().dropna()
        benchmark_returns = returns * 0.8

        metrics = MetricsCalculator.calculate_all_metrics(
            equity_curve=sample_equity_curve,
            trades=sample_trades,
            benchmark_returns=benchmark_returns,
            risk_free_rate=0.03
        )

        # 验证基准对比指标存在
        assert 'alpha' in metrics
        assert 'beta' in metrics
        assert 'information_ratio' in metrics
        assert 'tracking_error' in metrics

    def test_empty_data_handling(self):
        """测试空数据处理"""
        empty_curve = pd.Series([])
        empty_trades = []

        metrics = MetricsCalculator.calculate_all_metrics(
            equity_curve=empty_curve,
            trades=empty_trades
        )

        # 空数据应该返回空字典
        assert metrics == {}
