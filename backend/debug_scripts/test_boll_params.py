#!/usr/bin/env python3
"""测试布林带策略参数支持."""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.strategies.indicator.boll_breakout import BollBreakoutStrategy


def test_get_parameters():
    """测试获取参数定义."""
    print("=" * 60)
    print("测试 1: 获取参数定义")
    print("=" * 60)

    params = BollBreakoutStrategy.get_parameters()

    print(f"\n总共 {len(params)} 个参数:\n")
    for param in params:
        print(f"参数名: {param['name']}")
        print(f"  标签: {param['label']}")
        print(f"  类型: {param['type']}")
        print(f"  默认值: {param['default']}")
        print(f"  说明: {param['description']}")
        if 'options' in param:
            print(f"  选项: {[opt['label'] for opt in param['options']]}")
        if 'min' in param and 'max' in param:
            print(f"  范围: {param['min']} - {param['max']}")
        print()

    # 验证关键参数
    param_names = [p['name'] for p in params]
    required_params = ['period', 'std_dev', 'strategy_type', 'trend_ma_period', 'trend_position']

    print("验证必需参数:")
    for req_param in required_params:
        if req_param in param_names:
            print(f"  ✅ {req_param}")
        else:
            print(f"  ❌ {req_param} (缺失)")

    return params


def test_min_required_days():
    """测试最小数据天数计算."""
    print("\n" + "=" * 60)
    print("测试 2: 最小数据天数计算")
    print("=" * 60)

    test_cases = [
        ({}, "默认参数（period=20）"),
        ({'period': 20}, "period=20"),
        ({'period': 30}, "period=30"),
        ({'period': 20, 'trend_ma_period': 200}, "period=20, trend_ma_period=200"),
    ]

    for params, desc in test_cases:
        days = BollBreakoutStrategy.get_min_required_days(params)
        print(f"{desc}: {days}天")


def test_signal_generation():
    """测试信号生成（简单验证）."""
    print("\n" + "=" * 60)
    print("测试 3: 信号生成验证")
    print("=" * 60)

    import pandas as pd
    import numpy as np

    # 创建模拟数据
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    np.random.seed(42)

    # 创建一个有明显趋势的价格序列
    trend = np.linspace(100, 120, 50)
    noise = np.random.randn(50) * 2
    prices = trend + noise

    df = pd.DataFrame({
        'date': dates,
        'open': prices - 1,
        'high': prices + 2,
        'low': prices - 2,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 50)
    })

    strategy = BollBreakoutStrategy()

    # 测试均值回归模式（默认）
    print("\n测试均值回归模式:")
    params_mr = {
        'period': 20,
        'std_dev': 2.0,
        'strategy_type': 'mean_reversion'
    }
    df_mr = strategy.generate_signals(df.copy(), params_mr)
    buy_signals_mr = (df_mr['signal'] == 1).sum()
    sell_signals_mr = (df_mr['signal'] == -1).sum()
    print(f"  买入信号: {buy_signals_mr}个")
    print(f"  卖出信号: {sell_signals_mr}个")

    # 测试突破跟随模式
    print("\n测试突破跟随模式:")
    params_bo = {
        'period': 20,
        'std_dev': 2.0,
        'strategy_type': 'breakout'
    }
    df_bo = strategy.generate_signals(df.copy(), params_bo)
    buy_signals_bo = (df_bo['signal'] == 1).sum()
    sell_signals_bo = (df_bo['signal'] == -1).sum()
    print(f"  买入信号: {buy_signals_bo}个")
    print(f"  卖出信号: {sell_signals_bo}个")

    # 测试不同参数
    print("\n测试不同布林带参数:")
    test_params = [
        {'period': 10, 'std_dev': 1.5, 'strategy_type': 'mean_reversion'},
        {'period': 30, 'std_dev': 2.5, 'strategy_type': 'mean_reversion'},
    ]

    for params in test_params:
        df_test = strategy.generate_signals(df.copy(), params)
        buy_count = (df_test['signal'] == 1).sum()
        sell_count = (df_test['signal'] == -1).sum()
        print(f"  period={params['period']}, std_dev={params['std_dev']}: "
              f"买入{buy_count}个, 卖出{sell_count}个")


def main():
    """运行所有测试."""
    print("\n布林带策略参数支持测试\n")

    test_get_parameters()
    test_min_required_days()
    test_signal_generation()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
