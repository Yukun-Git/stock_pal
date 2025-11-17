"""调试脚本：测试小米集团MACD策略为何交易次数为零"""

import sys
import pandas as pd
from datetime import datetime, timedelta

# 添加app路径
sys.path.insert(0, '/app')

# 创建Flask应用上下文
from app import create_app
app = create_app()

from app.services.data_service import DataService
from app.services.indicator_service import IndicatorService
from app.strategies.indicator.macd_cross import MACDCrossStrategy


def debug_xiaomi_macd():
    """调试小米集团MACD策略"""

    print("=" * 80)
    print("调试：小米集团 MACD 策略 - 交易次数为零问题")
    print("=" * 80)

    # 1. 测试股票代码
    print("\n[步骤1] 测试股票代码和数据获取")
    print("-" * 80)

    # 小米可能的股票代码（港股）和备选A股股票
    possible_codes = [
        '01810',  # 港股小米
        '1810',   # 港股小米（无前导0）
        '600519', # 贵州茅台（A股，用于测试）
        '000001', # 平安银行（A股，用于测试）
    ]

    # 日期范围（最近一年）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    print(f"日期范围: {start_date_str} 至 {end_date_str}")

    df = None
    symbol = None

    for code in possible_codes:
        try:
            print(f"\n尝试获取股票代码: {code}")
            df = DataService.get_stock_data(code, start_date_str, end_date_str)
            if df is not None and len(df) > 0:
                symbol = code
                print(f"✓ 成功获取数据，共 {len(df)} 条记录")
                print(f"数据范围: {df.index[0]} 至 {df.index[-1]}")
                print(f"最新收盘价: {df.iloc[-1]['close']:.2f}")
                break
            else:
                print(f"✗ 数据为空")
        except Exception as e:
            print(f"✗ 获取失败: {str(e)}")

    if df is None or len(df) == 0:
        print("\n❌ 无法获取小米集团数据，可能是股票代码问题")
        print("提示：小米集团是港股，代码为 01810.HK")
        print("     当前系统主要支持A股数据")
        return

    # 2. 计算MACD指标
    print("\n[步骤2] 计算MACD指标")
    print("-" * 80)

    df = IndicatorService.calculate_macd(df)

    print("MACD指标计算完成")
    print(f"最新MACD值:")
    print(f"  DIF: {df.iloc[-1]['macd_dif']:.4f}")
    print(f"  DEA: {df.iloc[-1]['macd_dea']:.4f}")
    print(f"  柱状图: {df.iloc[-1]['macd_bar']:.4f}")

    # 显示最近10天的MACD数据
    print("\n最近10天MACD数据:")
    recent = df.tail(10)[['close', 'macd_dif', 'macd_dea', 'macd_bar']]
    print(recent.to_string())

    # 3. 生成交易信号
    print("\n[步骤3] 生成MACD金叉交易信号")
    print("-" * 80)

    strategy = MACDCrossStrategy()
    params = {
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'zero_line_filter': 'none',
        'second_cross_only': False,
        'use_divergence': False,
        'histogram_confirm': False,
        'histogram_increasing': False,
        'trend_ma_period': 0,
        'stop_loss_pct': 0
    }

    df_with_signals = strategy.generate_signals(df.copy(), params)

    # 统计信号
    buy_signals = df_with_signals[df_with_signals['signal'] == 1]
    sell_signals = df_with_signals[df_with_signals['signal'] == -1]

    print(f"买入信号数量: {len(buy_signals)}")
    print(f"卖出信号数量: {len(sell_signals)}")

    if len(buy_signals) > 0:
        print(f"\n买入信号明细:")
        for idx, row in buy_signals.iterrows():
            date_str = idx if isinstance(idx, str) else (idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else f"Day {idx}")
            print(f"  {date_str}: 价格={row['close']:.2f}, "
                  f"DIF={row['macd_dif']:.4f}, DEA={row['macd_dea']:.4f}")
    else:
        print("\n⚠️  没有生成任何买入信号！")

    if len(sell_signals) > 0:
        print(f"\n卖出信号明细:")
        for idx, row in sell_signals.iterrows():
            date_str = idx if isinstance(idx, str) else (idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else f"Day {idx}")
            print(f"  {date_str}: 价格={row['close']:.2f}, "
                  f"DIF={row['macd_dif']:.4f}, DEA={row['macd_dea']:.4f}")

    # 4. 分析金叉/死叉次数
    print("\n[步骤4] 分析金叉/死叉情况")
    print("-" * 80)

    golden_crosses = 0
    death_crosses = 0

    for i in range(1, len(df)):
        dif_prev = df.iloc[i-1]['macd_dif']
        dea_prev = df.iloc[i-1]['macd_dea']
        dif_curr = df.iloc[i]['macd_dif']
        dea_curr = df.iloc[i]['macd_dea']

        # 金叉: DIF上穿DEA
        if dif_prev <= dea_prev and dif_curr > dea_curr:
            golden_crosses += 1
            if golden_crosses <= 5:  # 只显示前5次
                idx = df.index[i]
                date_str = idx if isinstance(idx, str) else (idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else f"Day {i}")
                print(f"  金叉 #{golden_crosses}: {date_str}, "
                      f"价格={df.iloc[i]['close']:.2f}, DIF={dif_curr:.4f}, DEA={dea_curr:.4f}")

        # 死叉: DIF下穿DEA
        if dif_prev >= dea_prev and dif_curr < dea_curr:
            death_crosses += 1
            if death_crosses <= 5:  # 只显示前5次
                idx = df.index[i]
                date_str = idx if isinstance(idx, str) else (idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else f"Day {i}")
                print(f"  死叉 #{death_crosses}: {date_str}, "
                      f"价格={df.iloc[i]['close']:.2f}, DIF={dif_curr:.4f}, DEA={dea_curr:.4f}")

    print(f"\n总计: 金叉 {golden_crosses} 次, 死叉 {death_crosses} 次")

    # 5. 诊断问题
    print("\n[步骤5] 问题诊断")
    print("-" * 80)

    if golden_crosses == 0:
        print("❌ 问题：整个周期内没有出现金叉！")
        print("   可能原因：")
        print("   1. 股票一直处于下跌趋势，MACD持续死叉状态")
        print("   2. 数据周期太短，MACD指标还未完全形成")
        print("   3. MACD参数设置不适合该股票")
    elif len(buy_signals) == 0 and golden_crosses > 0:
        print(f"❌ 问题：虽然有 {golden_crosses} 次金叉，但策略没有生成买入信号！")
        print("   可能原因：")
        print("   1. 策略的过滤条件太严格")
        print("   2. 金叉发生时已经持仓，不能重复买入")
        print("   3. 策略代码存在bug")
    else:
        print(f"✓ 策略正常生成了 {len(buy_signals)} 个买入信号")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    with app.app_context():
        debug_xiaomi_macd()
