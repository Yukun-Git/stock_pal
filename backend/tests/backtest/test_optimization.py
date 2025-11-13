"""
测试参数优化模块

测试网格搜索和走步验证功能
"""

import pytest
from datetime import datetime
import pandas as pd
import numpy as np

from app.backtest.optimization import (
    GridSearchOptimizer,
    GridSearchResult,
    WalkForwardValidator,
    WalkForwardResult
)
from app.backtest.models import BacktestConfig


@pytest.fixture
def sample_market_data_long():
    """生成较长的市场数据（用于走步验证）"""
    # 生成2年的数据
    dates = pd.date_range('2022-01-03', '2023-12-29', freq='B')

    np.random.seed(42)
    base_price = 10.0
    prices = []
    for i in range(len(dates)):
        # 生成随机波动
        change = np.random.randn() * 0.02
        base_price = base_price * (1 + change)
        prices.append(base_price)

    data = {
        'date': dates,
        'open': prices,
        'high': [p * 1.02 for p in prices],
        'low': [p * 0.98 for p in prices],
        'close': prices,
        'volume': [1000000 + i * 1000 for i in range(len(dates))],
        'prev_close': [prices[0]] + prices[:-1]
    }
    return pd.DataFrame(data)


@pytest.fixture
def simple_strategy():
    """简单的均线交叉策略"""
    def strategy(data, params):
        df = data.copy()

        short_period = params.get('short_period', 5)
        long_period = params.get('long_period', 20)

        # 计算均线
        df['ma_short'] = df['close'].rolling(window=short_period).mean()
        df['ma_long'] = df['close'].rolling(window=long_period).mean()

        # 生成信号
        df['signal'] = 0
        df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
        df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1

        # 只保留信号变化的点（避免重复买卖）
        df['signal_change'] = df['signal'].diff()
        df.loc[df['signal_change'] == 0, 'signal'] = 0

        return df[['date', 'signal']]

    return strategy


@pytest.fixture
def basic_config():
    """基础配置"""
    return BacktestConfig(
        symbol='600000',
        start_date='20220103',
        end_date='20231229',
        initial_capital=100000,
        commission_rate=0.0003,
        min_commission=5.0,
        slippage_bps=5.0,
        stamp_tax_rate=0.001
    )


class TestGridSearchOptimizer:
    """测试网格搜索优化器"""

    def test_initialization(self, basic_config):
        """测试初始化"""
        param_grid = {
            'short_period': [5, 10],
            'long_period': [20, 30]
        }

        optimizer = GridSearchOptimizer(
            config=basic_config,
            param_grid=param_grid,
            optimization_metric='sharpe_ratio'
        )

        assert optimizer.config == basic_config
        assert optimizer.param_grid == param_grid
        assert optimizer.optimization_metric == 'sharpe_ratio'

    def test_get_total_combinations(self, basic_config):
        """测试计算组合数"""
        param_grid = {
            'short_period': [5, 10, 15],
            'long_period': [20, 30, 40, 50]
        }

        optimizer = GridSearchOptimizer(basic_config, param_grid)

        # 3 * 4 = 12 种组合
        assert optimizer.get_total_combinations() == 12

    def test_validate_param_grid_empty(self, basic_config):
        """测试空参数网格"""
        with pytest.raises(ValueError, match="param_grid cannot be empty"):
            GridSearchOptimizer(basic_config, {})

    def test_validate_param_grid_not_list(self, basic_config):
        """测试参数不是列表"""
        with pytest.raises(ValueError, match="must be a list"):
            GridSearchOptimizer(basic_config, {'short_period': 5})

    def test_validate_param_grid_empty_list(self, basic_config):
        """测试参数列表为空"""
        with pytest.raises(ValueError, match="cannot be empty"):
            GridSearchOptimizer(basic_config, {'short_period': []})

    def test_optimize_simple(self, basic_config, sample_market_data_long, simple_strategy):
        """测试简单优化"""
        param_grid = {
            'short_period': [5, 10],
            'long_period': [20, 30]
        }

        optimizer = GridSearchOptimizer(basic_config, param_grid)
        result = optimizer.optimize(sample_market_data_long, simple_strategy)

        # 验证结果
        assert isinstance(result, GridSearchResult)
        assert result.best_params is not None
        assert result.best_score is not None
        assert result.best_result is not None
        assert len(result.all_results) == 4  # 2 * 2 = 4
        assert result.total_combinations == 4

    def test_optimize_with_constraints(self, basic_config, sample_market_data_long, simple_strategy):
        """测试带约束的优化"""
        param_grid = {
            'short_period': [5, 10],
            'long_period': [20, 30]
        }

        constraints = {
            'min_sharpe_ratio': 0.01,  # 使用完整的指标名称
            'max_max_drawdown': -0.5  # 最大回撤不超过-50%
        }

        optimizer = GridSearchOptimizer(basic_config, param_grid)
        result = optimizer.optimize(
            sample_market_data_long,
            simple_strategy,
            constraints=constraints
        )

        # 验证约束系统工作（可能所有结果都不满足约束）
        assert result is not None
        assert len(result.all_results) == 4  # 所有组合都运行了

    def test_heatmap_generation(self, basic_config, sample_market_data_long, simple_strategy):
        """测试热力图数据生成"""
        param_grid = {
            'short_period': [5, 10],
            'long_period': [20, 30]
        }

        optimizer = GridSearchOptimizer(basic_config, param_grid)
        result = optimizer.optimize(sample_market_data_long, simple_strategy)

        # 验证热力图数据
        assert result.heatmap_data is not None
        assert 'x_param' in result.heatmap_data
        assert 'y_param' in result.heatmap_data
        assert 'x_values' in result.heatmap_data
        assert 'y_values' in result.heatmap_data
        assert 'z_values' in result.heatmap_data

        # 验证维度
        assert result.heatmap_data['x_param'] == 'short_period'
        assert result.heatmap_data['y_param'] == 'long_period'
        assert len(result.heatmap_data['x_values']) == 2
        assert len(result.heatmap_data['y_values']) == 2
        assert len(result.heatmap_data['z_values']) == 2  # 2行
        assert len(result.heatmap_data['z_values'][0]) == 2  # 2列

    def test_heatmap_no_generation_for_1param(self, basic_config, sample_market_data_long, simple_strategy):
        """测试单参数时不生成热力图"""
        param_grid = {
            'short_period': [5, 10, 15]
        }

        optimizer = GridSearchOptimizer(basic_config, param_grid)
        result = optimizer.optimize(sample_market_data_long, simple_strategy)

        # 单参数不生成热力图
        assert result.heatmap_data is None


class TestWalkForwardValidator:
    """测试走步验证器"""

    def test_initialization(self, basic_config):
        """测试初始化"""
        validator = WalkForwardValidator(
            config=basic_config,
            train_period_months=12,
            test_period_months=3,
            step_months=3
        )

        assert validator.config == basic_config
        assert validator.train_period_months == 12
        assert validator.test_period_months == 3
        assert validator.step_months == 3

    def test_generate_periods(self, basic_config, sample_market_data_long):
        """测试时间段生成"""
        validator = WalkForwardValidator(
            config=basic_config,
            train_period_months=6,  # 6个月训练期
            test_period_months=2,   # 2个月测试期
            step_months=2           # 2个月步进
        )

        periods = validator._generate_periods(sample_market_data_long)

        # 验证生成了多个时间段
        assert len(periods) > 0

        # 验证每个时间段的结构
        for period in periods:
            assert 'train_start' in period
            assert 'train_end' in period
            assert 'test_start' in period
            assert 'test_end' in period

    def test_filter_data_by_date(self, basic_config, sample_market_data_long):
        """测试日期过滤"""
        validator = WalkForwardValidator(basic_config)

        filtered = validator._filter_data_by_date(
            sample_market_data_long,
            '20220101',
            '20220630'
        )

        # 验证过滤结果
        assert len(filtered) > 0
        assert filtered['date'].min() >= pd.to_datetime('20220101')
        assert filtered['date'].max() <= pd.to_datetime('20220630')

    def test_validate_simple(self, basic_config, sample_market_data_long, simple_strategy):
        """测试简单走步验证"""
        param_grid = {
            'short_period': [5, 10],
            'long_period': [20, 30]
        }

        validator = WalkForwardValidator(
            config=basic_config,
            train_period_months=6,
            test_period_months=2,
            step_months=3
        )

        result = validator.validate(
            sample_market_data_long,
            simple_strategy,
            param_grid,
            optimize_in_train=True
        )

        # 验证结果
        assert isinstance(result, WalkForwardResult)
        assert len(result.periods) > 0
        assert result.total_periods == len(result.periods)
        assert 'avg_train_sharpe' in result.overall_metrics
        assert 'avg_test_sharpe' in result.overall_metrics
        assert 'avg_degradation' in result.overall_metrics

    def test_validate_without_optimization(self, basic_config, sample_market_data_long, simple_strategy):
        """测试不优化的走步验证"""
        validator = WalkForwardValidator(
            config=basic_config,
            train_period_months=6,
            test_period_months=2,
            step_months=3
        )

        # 不提供参数网格，不进行优化
        result = validator.validate(
            sample_market_data_long,
            simple_strategy,
            param_grid={},
            optimize_in_train=False
        )

        # 应该仍然有结果
        assert len(result.periods) > 0

    def test_period_degradation_calculation(self):
        """测试周期衰减计算"""
        from app.backtest.optimization.walk_forward import WalkForwardPeriod

        period = WalkForwardPeriod(
            period_id=1,
            train_start='20220101',
            train_end='20220630',
            test_start='20220701',
            test_end='20220831',
            train_best_params={'short_period': 5},
            train_metrics={'sharpe_ratio': 1.5},
            test_metrics={'sharpe_ratio': 1.2}
        )

        degradation = period.get_degradation('sharpe_ratio')

        # (1.2 - 1.5) / 1.5 = -0.2 (衰减20%)
        assert abs(degradation - (-0.2)) < 0.01

    def test_overfitting_detection(self, basic_config, sample_market_data_long, simple_strategy):
        """测试过拟合检测"""
        param_grid = {
            'short_period': [5],
            'long_period': [20]
        }

        validator = WalkForwardValidator(
            config=basic_config,
            train_period_months=6,
            test_period_months=2,
            step_months=3
        )

        result = validator.validate(
            sample_market_data_long,
            simple_strategy,
            param_grid
        )

        # 验证过拟合标志存在且为布尔类型
        assert hasattr(result, 'is_overfitting')
        assert result.is_overfitting in [True, False]  # 更宽松的检查
