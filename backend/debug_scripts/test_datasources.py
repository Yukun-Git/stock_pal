#!/usr/bin/env python3
"""
数据源测试脚本
测试各个候选数据源的可用性、性能和数据质量
"""

import time
import pandas as pd
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 测试配置
TEST_SYMBOL_A_SHARE = "000001"  # 平安银行 (A股)
TEST_SYMBOL_HK = "00700"  # 腾讯控股 (港股)
TEST_START_DATE = "20230101"
TEST_END_DATE = "20231231"


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_baostock():
    """测试 Baostock 数据源"""
    print_section("测试 Baostock 数据源")

    try:
        import baostock as bs

        # 登录
        lg = bs.login()
        if lg.error_code != '0':
            print(f"❌ Baostock 登录失败: {lg.error_msg}")
            return None

        print("✅ Baostock 登录成功")

        results = {
            "name": "Baostock",
            "display_name": "证券宝",
            "markets": ["A-share"],
            "requires_auth": False,
            "tests": {}
        }

        # 测试1: 获取股票数据
        print("\n测试1: 获取A股历史数据 (000001)")
        start_time = time.time()

        rs = bs.query_history_k_data_plus(
            f"sz.{TEST_SYMBOL_A_SHARE}",
            "date,code,open,high,low,close,volume,amount",
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE,
            frequency="d",
            adjustflag="3"
        )

        if rs.error_code != '0':
            print(f"❌ 获取数据失败: {rs.error_msg}")
            results["tests"]["get_data"] = {"success": False, "error": rs.error_msg}
        else:
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            response_time = (time.time() - start_time) * 1000

            print(f"✅ 获取数据成功")
            print(f"   数据行数: {len(df)}")
            print(f"   响应时间: {response_time:.2f}ms")
            print(f"   列名: {df.columns.tolist()}")
            print(f"   数据预览:\n{df.head()}")

            results["tests"]["get_data"] = {
                "success": True,
                "rows": len(df),
                "response_time_ms": response_time,
                "columns": df.columns.tolist()
            }

        # 测试2: 搜索股票
        print("\n测试2: 搜索股票 (平安)")
        start_time = time.time()

        # Baostock 获取所有股票列表
        rs = bs.query_stock_basic()
        if rs.error_code != '0':
            print(f"❌ 搜索失败: {rs.error_msg}")
            results["tests"]["search"] = {"success": False, "error": rs.error_msg}
        else:
            stock_list = []
            while (rs.error_code == '0') & rs.next():
                stock_list.append(rs.get_row_data())

            stock_df = pd.DataFrame(stock_list, columns=rs.fields)

            # 搜索包含"平安"的股票
            search_result = stock_df[stock_df['code_name'].str.contains('平安', na=False)]
            response_time = (time.time() - start_time) * 1000

            print(f"✅ 搜索成功")
            print(f"   总股票数: {len(stock_df)}")
            print(f"   匹配结果: {len(search_result)}")
            print(f"   响应时间: {response_time:.2f}ms")
            if len(search_result) > 0:
                print(f"   结果预览:\n{search_result[['code', 'code_name']].head()}")

            results["tests"]["search"] = {
                "success": True,
                "total_stocks": len(stock_df),
                "matched": len(search_result),
                "response_time_ms": response_time
            }

        # 登出
        bs.logout()

        results["overall"] = "✅ 可用"
        return results

    except ImportError:
        print("❌ Baostock 库未安装")
        print("   安装命令: pip install baostock")
        return {
            "name": "Baostock",
            "overall": "❌ 未安装",
            "error": "Library not installed"
        }
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return {
            "name": "Baostock",
            "overall": "❌ 失败",
            "error": str(e)
        }


def test_tushare():
    """测试 Tushare 数据源"""
    print_section("测试 Tushare 数据源")

    try:
        import tushare as ts

        # 注意: Tushare 需要token
        # 可以从环境变量或配置文件读取
        token = os.environ.get('TUSHARE_TOKEN', '')

        if not token:
            print("⚠️  Tushare 需要 Token")
            print("   1. 注册账号: https://tushare.pro/register")
            print("   2. 获取积分: https://tushare.pro/document/1?doc_id=13")
            print("   3. 设置环境变量: export TUSHARE_TOKEN='your_token'")
            return {
                "name": "Tushare",
                "overall": "⚠️  需要Token",
                "requires_auth": True,
                "note": "需要注册并获取积分"
            }

        ts.set_token(token)
        pro = ts.pro_api()

        results = {
            "name": "Tushare",
            "display_name": "Tushare Pro",
            "markets": ["A-share"],
            "requires_auth": True,
            "tests": {}
        }

        # 测试1: 获取股票数据
        print("\n测试1: 获取A股历史数据 (000001.SZ)")
        start_time = time.time()

        df = pro.daily(
            ts_code='000001.SZ',
            start_date=TEST_START_DATE,
            end_date=TEST_END_DATE
        )

        response_time = (time.time() - start_time) * 1000

        print(f"✅ 获取数据成功")
        print(f"   数据行数: {len(df)}")
        print(f"   响应时间: {response_time:.2f}ms")
        print(f"   列名: {df.columns.tolist()}")
        print(f"   数据预览:\n{df.head()}")

        results["tests"]["get_data"] = {
            "success": True,
            "rows": len(df),
            "response_time_ms": response_time,
            "columns": df.columns.tolist()
        }

        # 测试2: 搜索股票
        print("\n测试2: 搜索股票 (平安)")
        start_time = time.time()

        stock_list = pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,market'
        )

        search_result = stock_list[stock_list['name'].str.contains('平安', na=False)]
        response_time = (time.time() - start_time) * 1000

        print(f"✅ 搜索成功")
        print(f"   总股票数: {len(stock_list)}")
        print(f"   匹配结果: {len(search_result)}")
        print(f"   响应时间: {response_time:.2f}ms")
        if len(search_result) > 0:
            print(f"   结果预览:\n{search_result[['ts_code', 'name']].head()}")

        results["tests"]["search"] = {
            "success": True,
            "total_stocks": len(stock_list),
            "matched": len(search_result),
            "response_time_ms": response_time
        }

        results["overall"] = "✅ 可用"
        return results

    except ImportError:
        print("❌ Tushare 库未安装")
        print("   安装命令: pip install tushare")
        return {
            "name": "Tushare",
            "overall": "❌ 未安装",
            "error": "Library not installed"
        }
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

        # 检查是否是积分不足
        if "抱歉" in str(e) or "权限" in str(e) or "积分" in str(e):
            print("   可能原因: 积分不足或权限不够")
            return {
                "name": "Tushare",
                "overall": "⚠️  积分不足",
                "error": str(e),
                "note": "需要更多积分才能访问"
            }

        return {
            "name": "Tushare",
            "overall": "❌ 失败",
            "error": str(e)
        }


def test_akshare_advanced():
    """测试 AkShare 的高级功能 (港股支持)"""
    print_section("测试 AkShare 高级功能")

    try:
        import akshare as ak

        results = {
            "name": "AkShare (Advanced)",
            "markets_tested": [],
            "tests": {}
        }

        # 测试港股数据
        print("\n测试: 获取港股数据 (腾讯控股 00700)")
        start_time = time.time()

        try:
            # 尝试获取港股实时行情
            hk_spot = ak.stock_hk_spot()
            response_time = (time.time() - start_time) * 1000

            # 搜索腾讯
            search_result = hk_spot[hk_spot['名称'].str.contains('腾讯', na=False)]

            print(f"✅ 获取港股数据成功")
            print(f"   总股票数: {len(hk_spot)}")
            print(f"   匹配结果: {len(search_result)}")
            print(f"   响应时间: {response_time:.2f}ms")
            if len(search_result) > 0:
                print(f"   结果预览:\n{search_result[['代码', '名称', '最新价']].head()}")

            results["markets_tested"].append("HK")
            results["tests"]["hk_stocks"] = {
                "success": True,
                "total_stocks": len(hk_spot),
                "response_time_ms": response_time
            }

        except Exception as e:
            print(f"❌ 港股数据获取失败: {str(e)}")
            results["tests"]["hk_stocks"] = {
                "success": False,
                "error": str(e)
            }

        results["overall"] = "✅ 部分可用"
        return results

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return {
            "name": "AkShare (Advanced)",
            "overall": "❌ 失败",
            "error": str(e)
        }


def generate_summary(all_results):
    """生成测试摘要"""
    print_section("测试摘要")

    print("\n数据源可用性:")
    print("-" * 80)
    print(f"{'数据源':<20} {'状态':<15} {'市场支持':<20} {'需要认证':<10}")
    print("-" * 80)

    for result in all_results:
        name = result.get('name', 'Unknown')
        overall = result.get('overall', '未知')
        markets = ', '.join(result.get('markets', result.get('markets_tested', [])))
        requires_auth = '是' if result.get('requires_auth', False) else '否'

        print(f"{name:<20} {overall:<15} {markets:<20} {requires_auth:<10}")

    print("\n性能对比 (响应时间):")
    print("-" * 80)
    print(f"{'数据源':<20} {'获取数据':<15} {'搜索股票':<15}")
    print("-" * 80)

    for result in all_results:
        name = result.get('name', 'Unknown')
        tests = result.get('tests', {})

        get_data_time = tests.get('get_data', {}).get('response_time_ms', '-')
        search_time = tests.get('search', {}).get('response_time_ms', '-')

        get_data_str = f"{get_data_time:.0f}ms" if isinstance(get_data_time, (int, float)) else '-'
        search_str = f"{search_time:.0f}ms" if isinstance(search_time, (int, float)) else '-'

        print(f"{name:<20} {get_data_str:<15} {search_str:<15}")

    print("\n推荐实施优先级:")
    print("-" * 80)

    # 根据测试结果给出推荐
    recommendations = []

    for result in all_results:
        name = result.get('name', 'Unknown')
        overall = result.get('overall', '')

        if '✅' in overall:
            requires_auth = result.get('requires_auth', False)
            tests = result.get('tests', {})
            get_data_success = tests.get('get_data', {}).get('success', False)

            if get_data_success:
                if requires_auth:
                    priority = "中优先级"
                else:
                    priority = "高优先级"

                recommendations.append({
                    "name": name,
                    "priority": priority,
                    "reason": "测试通过" + (" (需要认证)" if requires_auth else " (无需认证)")
                })
        elif '⚠️' in overall:
            recommendations.append({
                "name": name,
                "priority": "待评估",
                "reason": result.get('note', '需要进一步配置')
            })

    for rec in recommendations:
        print(f"{rec['priority']}: {rec['name']} - {rec['reason']}")

    return recommendations


def main():
    """主函数"""
    print("=" * 80)
    print("  数据源测试工具")
    print("  测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)

    all_results = []

    # 测试 Baostock
    result = test_baostock()
    if result:
        all_results.append(result)

    # 测试 Tushare
    result = test_tushare()
    if result:
        all_results.append(result)

    # 测试 AkShare 高级功能
    result = test_akshare_advanced()
    if result:
        all_results.append(result)

    # 生成摘要
    recommendations = generate_summary(all_results)

    # 保存结果到文件
    import json
    output_file = os.path.join(os.path.dirname(__file__), 'datasource_test_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": datetime.now().isoformat(),
            "results": all_results,
            "recommendations": recommendations
        }, f, ensure_ascii=False, indent=2)

    print(f"\n测试结果已保存到: {output_file}")


if __name__ == "__main__":
    main()
