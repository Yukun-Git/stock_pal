"""
调试基准对比指标计算

运行方式：
docker-compose exec backend python3 debug_scripts/debug_benchmark_metrics.py
"""

from app import create_app
from app.backtest.orchestrator import BacktestOrchestrator, BacktestConfig
from app.services.benchmark_service import BenchmarkService
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # 配置回测参数
    config = BacktestConfig(
        symbol='600519',  # 贵州茅台
        strategy_id='ma_cross',
        start_date='20240101',
        end_date=datetime.now().strftime('%Y%m%d'),
        initial_capital=100000,
        commission_rate=0.0003,
        benchmark_id='CSI300'  # 对比沪深300
    )

    # 执行回测
    print("执行回测...")
    orchestrator = BacktestOrchestrator(config)
    result = orchestrator.run()

    # 获取策略收益率
    equity_curve = result.equity_curve.set_index('date')['equity']
    strategy_returns = equity_curve.pct_change().dropna()

    # 获取基准数据
    print("\n获取基准数据...")
    benchmark_df = BenchmarkService.get_benchmark_data(
        'CSI300',
        config.start_date,
        config.end_date
    )
    benchmark_returns = BenchmarkService.calculate_benchmark_returns(benchmark_df)

    # 对齐日期
    aligned_strategy, aligned_benchmark = strategy_returns.align(
        benchmark_returns,
        join='inner'
    )

    print("\n" + "="*60)
    print("数据统计")
    print("="*60)

    print(f"\n策略收益率序列:")
    print(f"  数据点数: {len(strategy_returns)}")
    print(f"  日期范围: {strategy_returns.index[0]} 到 {strategy_returns.index[-1]}")
    print(f"  均值: {strategy_returns.mean():.6f}")
    print(f"  标准差: {strategy_returns.std():.6f}")
    print(f"  最小值: {strategy_returns.min():.6f}")
    print(f"  最大值: {strategy_returns.max():.6f}")

    print(f"\n基准收益率序列:")
    print(f"  数据点数: {len(benchmark_returns)}")
    print(f"  日期范围: {benchmark_returns.index[0]} 到 {benchmark_returns.index[-1]}")
    print(f"  均值: {benchmark_returns.mean():.6f}")
    print(f"  标准差: {benchmark_returns.std():.6f}")
    print(f"  最小值: {benchmark_returns.min():.6f}")
    print(f"  最大值: {benchmark_returns.max():.6f}")

    print(f"\n对齐后:")
    print(f"  策略数据点: {len(aligned_strategy)}")
    print(f"  基准数据点: {len(aligned_benchmark)}")

    # 计算超额收益
    excess_returns = aligned_strategy - aligned_benchmark
    print(f"\n超额收益统计:")
    print(f"  均值: {excess_returns.mean():.6f}")
    print(f"  标准差: {excess_returns.std():.6f}")
    print(f"  最小值: {excess_returns.min():.6f}")
    print(f"  最大值: {excess_returns.max():.6f}")

    print("\n" + "="*60)
    print("基准对比指标")
    print("="*60)

    print(f"\nAlpha: {result.metrics.get('alpha', 0):.6f}")
    print(f"Beta: {result.metrics.get('beta', 0):.6f}")
    print(f"信息比率: {result.metrics.get('information_ratio', 0):.6f}")
    print(f"跟踪误差: {result.metrics.get('tracking_error', 0):.6f}")

    print(f"\n策略年化收益: {result.metrics.get('cagr', 0):.4f} ({result.metrics.get('cagr', 0)*100:.2f}%)")
    print(f"策略总收益: {result.metrics.get('total_return', 0):.4f} ({result.metrics.get('total_return', 0)*100:.2f}%)")

    # 手动计算基准的总收益和年化
    import numpy as np
    benchmark_equity = benchmark_df.set_index('date')['close']
    benchmark_total_return = (benchmark_equity.iloc[-1] - benchmark_equity.iloc[0]) / benchmark_equity.iloc[0]

    # 计算天数
    days = (benchmark_equity.index[-1] - benchmark_equity.index[0]).days
    years = days / 365.25
    benchmark_cagr = (1 + benchmark_total_return) ** (1 / years) - 1 if years > 0 else 0

    print(f"\n基准年化收益: {benchmark_cagr:.4f} ({benchmark_cagr*100:.2f}%)")
    print(f"基准总收益: {benchmark_total_return:.4f} ({benchmark_total_return*100:.2f}%)")

    print(f"\n超额收益 (总收益差): {(result.metrics.get('total_return', 0) - benchmark_total_return)*100:.2f}%")
    print(f"超额收益 (年化差): {(result.metrics.get('cagr', 0) - benchmark_cagr)*100:.2f}%")
