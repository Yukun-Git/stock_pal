#!/usr/bin/env python3
"""测试故障转移功能.

验证当首选数据源失败时，系统能自动切换到备用数据源。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.failover_service import FailoverService


def test_failover():
    """测试故障转移."""
    print("=" * 60)
    print("测试故障转移功能")
    print("=" * 60)

    # 创建服务实例
    service = FailoverService()

    # 测试1: A股数据获取 (应该使用 akshare)
    print("\n[测试1] 获取A股数据 (000001)")
    try:
        df, adapter = service.get_stock_data_with_failover(
            '000001', '20231201', '20231205'
        )
        print(f"  ✓ 成功! 使用适配器: {adapter}")
        print(f"  数据行数: {len(df)}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")

    # 测试2: 港股数据获取 (优先 yfinance，可能失败并切换到 akshare)
    print("\n[测试2] 获取港股数据 (00700.HK)")
    try:
        df, adapter = service.get_stock_data_with_failover(
            '00700.HK', '20231201', '20231205'
        )
        print(f"  ✓ 成功! 使用适配器: {adapter}")
        print(f"  数据行数: {len(df)}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")

    # 测试3: 指定优先适配器
    print("\n[测试3] 指定使用 baostock 获取 000001")
    try:
        df, adapter = service.get_stock_data_with_failover(
            '000001', '20231201', '20231205',
            preferred_adapter='baostock'
        )
        print(f"  ✓ 成功! 使用适配器: {adapter}")
        print(f"  数据行数: {len(df)}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")

    # 测试4: 搜索功能
    print("\n[测试4] 搜索股票 '平安'")
    try:
        results, adapter = service.search_stock_with_failover('平安')
        print(f"  ✓ 成功! 使用适配器: {adapter}")
        print(f"  找到 {len(results)} 只股票")
        if results:
            print(f"  示例: {results[0].get('code')} - {results[0].get('name')}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")

    # 显示性能指标
    print("\n" + "=" * 60)
    print("性能指标")
    print("=" * 60)
    metrics = service.get_metrics()
    for name, data in metrics.items():
        success = data.get('success_count', 0)
        fail = data.get('fail_count', 0)
        avg_ms = data.get('avg_response_ms', 0)
        print(f"\n{name}:")
        print(f"  成功: {success}, 失败: {fail}")
        if avg_ms:
            print(f"  平均响应时间: {avg_ms:.2f}ms")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_failover()
