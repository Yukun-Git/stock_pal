"""
测试回测编排器

测试 BacktestOrchestrator 的完整回测流程
"""

import pytest
from datetime import datetime
import pandas as pd

from app.backtest.orchestrator import BacktestOrchestrator
from app.backtest.models import (
    BacktestConfig,
    TradingEnvironment,
    Signal,
    StockInfo
)


@pytest.fixture
def sample_market_data():
    """生成示例市场数据"""
    dates = pd.date_range('2024-01-02', '2024-01-31', freq='B')
    data = {
        'date': dates,
        'open': [10.0 + i * 0.05 for i in range(len(dates))],
        'high': [10.2 + i * 0.05 for i in range(len(dates))],
        'low': [9.8 + i * 0.05 for i in range(len(dates))],
        'close': [10.1 + i * 0.05 for i in range(len(dates))],
        'volume': [1000000 + i * 10000 for i in range(len(dates))],
        'prev_close': [10.0 + i * 0.05 for i in range(len(dates))]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_signals():
    """生成示例交易信号"""
    dates = pd.date_range('2024-01-02', '2024-01-31', freq='B')
    signals = [0] * len(dates)

    # 第3天买入
    signals[2] = 1
    # 第10天卖出
    signals[9] = -1
    # 第15天买入
    signals[14] = 1
    # 第20天卖出
    signals[19] = -1

    data = {
        'date': dates,
        'signal': signals
    }
    return pd.DataFrame(data)


@pytest.fixture
def simple_config():
    """简单的回测配置"""
    return BacktestConfig(
        symbol='600000',
        start_date='20240102',
        end_date='20240131',
        initial_capital=100000,
        commission_rate=0.0003,
        min_commission=5.0,
        slippage_bps=5.0,
        stamp_tax_rate=0.001
    )


class TestBacktestOrchestrator:
    """测试回测编排器"""

    def test_initialization(self, simple_config):
        """测试初始化"""
        orchestrator = BacktestOrchestrator(simple_config)

        assert orchestrator.config == simple_config
        assert orchestrator.backtest_id is not None
        assert orchestrator.backtest_id.startswith('bt_')
        assert orchestrator.calendar is not None
        assert orchestrator.trading_engine is not None
        assert orchestrator.metrics_calculator is not None
        assert orchestrator.environment is not None

    def test_identify_environment(self, simple_config):
        """测试环境识别"""
        orchestrator = BacktestOrchestrator(simple_config)

        # 600000 应该被识别为主板
        assert orchestrator.environment.market == 'CN'
        assert orchestrator.environment.board == 'MAIN'
        assert orchestrator.environment.channel == 'DIRECT'

    def test_identify_environment_gem(self):
        """测试创业板识别"""
        config = BacktestConfig(
            symbol='300001',  # 创业板
            start_date='20240102',
            end_date='20240131',
            initial_capital=100000
        )
        orchestrator = BacktestOrchestrator(config)

        assert orchestrator.environment.board == 'GEM'

    def test_identify_environment_star(self):
        """测试科创板识别"""
        config = BacktestConfig(
            symbol='688001',  # 科创板
            start_date='20240102',
            end_date='20240131',
            initial_capital=100000
        )
        orchestrator = BacktestOrchestrator(config)

        assert orchestrator.environment.board == 'STAR'

    def test_prepare_data(self, simple_config, sample_market_data, sample_signals):
        """测试数据准备"""
        orchestrator = BacktestOrchestrator(simple_config)

        df = orchestrator._prepare_data(sample_market_data, sample_signals)

        # 检查数据合并正确
        assert len(df) == len(sample_market_data)
        assert 'signal' in df.columns
        assert 'date' in df.columns
        assert 'close' in df.columns

        # 检查信号列存在且正确
        assert df['signal'].notna().all()
        assert df['signal'].iloc[2] == 1  # 第3天买入
        assert df['signal'].iloc[9] == -1  # 第10天卖出

    def test_run_empty_signals(self, simple_config, sample_market_data):
        """测试无交易信号的回测"""
        orchestrator = BacktestOrchestrator(simple_config)

        # 创建全0信号
        signals = pd.DataFrame({
            'date': sample_market_data['date'],
            'signal': [0] * len(sample_market_data)
        })

        result = orchestrator.run(sample_market_data, signals)

        # 验证结果
        assert result is not None
        assert result.config == simple_config
        assert len(result.trades) == 0  # 无交易
        assert result.equity_curve is not None
        assert len(result.equity_curve) > 0

        # 无交易，最终资金应该等于初始资金
        final_equity = result.equity_curve['equity'].iloc[-1]
        assert abs(final_equity - simple_config.initial_capital) < 0.01

    def test_run_with_trades(self, simple_config, sample_market_data, sample_signals):
        """测试有交易的回测"""
        orchestrator = BacktestOrchestrator(simple_config)

        result = orchestrator.run(sample_market_data, sample_signals)

        # 验证结果
        assert result is not None
        assert len(result.trades) > 0  # 应该有交易
        assert result.equity_curve is not None
        assert len(result.equity_curve) > 0

        # 验证指标存在
        assert 'total_return' in result.metrics
        assert 'max_drawdown' in result.metrics
        assert 'sharpe_ratio' in result.metrics

        # 验证元数据
        assert 'backtest_id' in result.metadata
        assert 'execution_time_seconds' in result.metadata
        assert 'total_trades' in result.metadata
        assert result.metadata['total_trades'] == len(result.trades)

    def test_metadata_recording(self, simple_config, sample_market_data, sample_signals):
        """测试元数据记录"""
        orchestrator = BacktestOrchestrator(simple_config)

        result = orchestrator.run(sample_market_data, sample_signals)

        # 验证元数据完整性
        metadata = result.metadata
        assert 'backtest_id' in metadata
        assert 'engine_version' in metadata
        assert 'environment' in metadata
        assert 'started_at' in metadata
        assert 'completed_at' in metadata
        assert 'execution_time_seconds' in metadata
        assert 'data_points' in metadata
        assert 'trading_days' in metadata
        assert 'total_orders' in metadata
        assert 'total_trades' in metadata

        # 验证版本信息
        assert metadata['engine_version'] == '2.0.0'
        assert 'CN_MAIN' in metadata['environment']

    def test_run_with_stock_info(self, simple_config, sample_market_data, sample_signals):
        """测试带股票信息的回测"""
        orchestrator = BacktestOrchestrator(simple_config)

        stock_info = StockInfo(
            symbol='600000',
            name='浦发银行',
            board='MAIN',
            ipo_date=datetime(2000, 1, 1)
        )

        result = orchestrator.run(
            sample_market_data,
            sample_signals,
            stock_info=stock_info
        )

        assert result is not None
        assert len(result.trades) > 0

    def test_equity_curve_structure(self, simple_config, sample_market_data, sample_signals):
        """测试权益曲线结构"""
        orchestrator = BacktestOrchestrator(simple_config)

        result = orchestrator.run(sample_market_data, sample_signals)

        # 验证权益曲线结构
        equity_curve = result.equity_curve
        assert 'date' in equity_curve.columns
        assert 'equity' in equity_curve.columns
        assert 'cash' in equity_curve.columns
        assert 'position_value' in equity_curve.columns

        # 验证数据类型
        assert pd.api.types.is_datetime64_any_dtype(equity_curve['date'])

        # 验证权益 = 现金 + 持仓市值
        for idx, row in equity_curve.iterrows():
            assert abs(row['equity'] - (row['cash'] + row['position_value'])) < 0.01

    def test_performance_metrics_calculation(self, simple_config, sample_market_data, sample_signals):
        """测试性能指标计算"""
        orchestrator = BacktestOrchestrator(simple_config)

        result = orchestrator.run(sample_market_data, sample_signals)

        metrics = result.metrics

        # 验证所有必需指标存在
        required_metrics = [
            'total_return', 'cagr', 'annual_return',
            'volatility', 'max_drawdown', 'max_drawdown_duration',
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
            'win_rate', 'profit_factor', 'avg_trade_return',
            'total_trades',
            'turnover_rate', 'avg_holding_period'
        ]

        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"

    def test_run_with_strategy_func(self, simple_config, sample_market_data):
        """测试使用策略函数运行"""
        orchestrator = BacktestOrchestrator(simple_config)

        def simple_strategy(data, params):
            """简单的移动平均策略"""
            df = data.copy()

            # 计算5日均线
            df['ma5'] = df['close'].rolling(window=5).mean()

            # 生成信号
            df['signal'] = 0
            df.loc[df['close'] > df['ma5'], 'signal'] = 1
            df.loc[df['close'] < df['ma5'], 'signal'] = -1

            return df[['date', 'signal']]

        result = orchestrator.run_with_strategy(
            sample_market_data,
            simple_strategy,
            strategy_params={}
        )

        assert result is not None
        assert result.equity_curve is not None

    def test_multiple_runs_isolation(self, simple_config, sample_market_data, sample_signals):
        """测试多次运行的隔离性"""
        orchestrator1 = BacktestOrchestrator(simple_config)
        orchestrator2 = BacktestOrchestrator(simple_config)

        result1 = orchestrator1.run(sample_market_data, sample_signals)
        result2 = orchestrator2.run(sample_market_data, sample_signals)

        # 验证两次运行结果一致
        assert abs(result1.metrics['total_return'] - result2.metrics['total_return']) < 0.01
        assert len(result1.trades) == len(result2.trades)

        # 验证回测ID不同
        assert result1.metadata['backtest_id'] != result2.metadata['backtest_id']

    def test_generate_backtest_id(self, simple_config):
        """测试回测ID生成"""
        orchestrator1 = BacktestOrchestrator(simple_config)
        orchestrator2 = BacktestOrchestrator(simple_config)

        # 每次生成的ID应该不同
        assert orchestrator1.backtest_id != orchestrator2.backtest_id

        # ID格式验证
        assert orchestrator1.backtest_id.startswith('bt_')
        assert len(orchestrator1.backtest_id) > 10
