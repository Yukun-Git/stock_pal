#!/usr/bin/env python3
"""
测试新回测引擎API集成

测试：
1. 回测API（基础功能）
2. 回测API（增强指标）
3. 优化API
"""

import requests
import json
from datetime import datetime, timedelta


BASE_URL = "http://localhost:4001"


def test_health():
    """测试健康检查"""
    print("Testing /health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"✓ Health check: {response.json()}")
    return response.status_code == 200


def test_strategies_list():
    """测试策略列表"""
    print("\nTesting /api/v1/strategies...")
    response = requests.get(f"{BASE_URL}/api/v1/strategies")
    data = response.json()

    if data['success']:
        print(f"✓ Found {len(data['data'])} strategies")
        return True, data['data']
    else:
        print(f"✗ Failed: {data.get('error')}")
        return False, None


def test_backtest(strategy_id='ma_cross'):
    """测试回测API（使用新引擎）"""
    print(f"\nTesting /api/v1/backtest with {strategy_id}...")

    # 计算日期（最近1年）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    payload = {
        "symbol": "600000",
        "strategy_id": strategy_id,
        "start_date": start_date.strftime('%Y%m%d'),
        "end_date": end_date.strftime('%Y%m%d'),
        "initial_capital": 100000,
        "commission_rate": 0.0003,
        "min_commission": 5.0,
        "slippage_bps": 5.0,
        "stamp_tax_rate": 0.001,
        "strategy_params": {
            "short_period": 10,
            "long_period": 60
        }
    }

    response = requests.post(f"{BASE_URL}/api/v1/backtest", json=payload)
    data = response.json()

    if data['success']:
        results = data['data']['results']
        print(f"✓ Backtest completed:")
        print(f"  - Total Return: {results['total_return']:.2%}")
        print(f"  - Sharpe Ratio: {results.get('sharpe_ratio', 'N/A')}")
        print(f"  - Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"  - Total Trades: {results['total_trades']}")
        print(f"  - Win Rate: {results['win_rate']:.2%}")

        # 检查新指标
        if 'cagr' in results:
            print(f"  - CAGR: {results['cagr']:.2%}")
            print(f"  - Sortino Ratio: {results.get('sortino_ratio', 'N/A')}")
            print(f"  - Calmar Ratio: {results.get('calmar_ratio', 'N/A')}")

        # 检查元数据
        if 'metadata' in data['data']:
            metadata = data['data']['metadata']
            print(f"  - Backtest ID: {metadata.get('backtest_id', 'N/A')}")
            print(f"  - Execution Time: {metadata.get('execution_time_seconds', 'N/A')}s")

        return True
    else:
        print(f"✗ Failed: {data.get('error')}")
        return False


def test_optimize():
    """测试参数优化API"""
    print("\nTesting /api/v1/backtest/optimize...")

    # 计算日期（最近2年，优化需要更多数据）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    payload = {
        "symbol": "600000",
        "strategy_id": "ma_cross",
        "start_date": start_date.strftime('%Y%m%d'),
        "end_date": end_date.strftime('%Y%m%d'),
        "initial_capital": 100000,
        "param_grid": {
            "short_period": [5, 10],
            "long_period": [30, 60]
        },
        "optimization_metric": "sharpe_ratio"
    }

    print("  Running optimization (4 combinations)...")
    response = requests.post(f"{BASE_URL}/api/v1/backtest/optimize", json=payload, timeout=60)
    data = response.json()

    if data['success']:
        result = data['data']
        print(f"✓ Optimization completed:")
        print(f"  - Best Params: {result['best_params']}")
        print(f"  - Best Score: {result['best_score']:.4f}")
        print(f"  - Total Combinations: {result['total_combinations']}")
        print(f"  - Execution Time: {result['execution_time']:.2f}s")

        # 显示热力图数据
        if result.get('heatmap_data'):
            print(f"  - Heatmap: Available ({len(result['heatmap_data']['z_values'])}x{len(result['heatmap_data']['z_values'][0])})")

        return True
    else:
        print(f"✗ Failed: {data.get('error')}")
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("回测引擎 API 集成测试")
    print("="*60)

    tests = []

    # 测试1: 健康检查
    tests.append(("Health Check", test_health()))

    # 测试2: 策略列表
    success, strategies = test_strategies_list()
    tests.append(("Strategy List", success))

    # 测试3: 回测API
    if strategies:
        tests.append(("Backtest API", test_backtest(strategies[0]['id'])))
    else:
        tests.append(("Backtest API", test_backtest()))

    # 测试4: 优化API
    tests.append(("Optimize API", test_optimize()))

    # 汇总
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for name, result in tests:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")
    print("="*60)

    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
