"""调试MACD策略 - 分析为何没有产生交易信号"""

import sys
sys.path.insert(0, '/app')

from datetime import datetime, timedelta
import pandas as pd

# 创建Flask应用上下文
from app import create_app
app = create_app()


def debug_macd_strategy(symbol='01810.HK', days=365):
    """调试MACD策略信号生成"""
    from app.services.data_service import DataService
    from app.strategies.indicator.macd_cross import MACDCrossStrategy

    print(f"\n{'='*60}")
    print(f"调试MACD策略 - {symbol}")
    print(f"{'='*60}\n")

    # 1. 获取数据
    print("1. 获取历史数据...")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = DataService.get_stock_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d'),
            adjust='qfq'
        )
        print(f"   ✓ 成功获取 {len(df)} 条数据")
        print(f"   日期范围: {df.iloc[0]['date']} 到 {df.iloc[-1]['date']}")
    except Exception as e:
        print(f"   ✗ 获取数据失败: {e}")
        return

    # 2. 初始化策略
    print("\n2. 初始化MACD策略...")
    strategy = MACDCrossStrategy()

    # 默认参数
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
    print(f"   参数: {params}")

    # 3. 生成信号
    print("\n3. 生成交易信号...")
    df_with_signals = strategy.generate_signals(df, params)

    # 4. 分析信号
    buy_signals = df_with_signals[df_with_signals['signal'] == 1]
    sell_signals = df_with_signals[df_with_signals['signal'] == -1]

    print(f"\n   买入信号数量: {len(buy_signals)}")
    print(f"   卖出信号数量: {len(sell_signals)}")

    if len(buy_signals) > 0:
        print(f"\n   买入信号详情:")
        for idx, row in buy_signals.iterrows():
            print(f"   - {row['date']}: 价格={row['close']:.2f}, DIF={row['macd_dif']:.4f}, DEA={row['macd_dea']:.4f}")
    else:
        print(f"\n   ⚠️  没有买入信号！")

    # 5. 分析MACD金叉情况
    print("\n4. 分析MACD金叉/死叉情况...")

    golden_crosses = 0
    death_crosses = 0

    for i in range(1, len(df_with_signals)):
        dif_prev = df_with_signals.iloc[i-1]['macd_dif']
        dea_prev = df_with_signals.iloc[i-1]['macd_dea']
        dif_curr = df_with_signals.iloc[i]['macd_dif']
        dea_curr = df_with_signals.iloc[i]['macd_dea']

        if dif_prev <= dea_prev and dif_curr > dea_curr:
            golden_crosses += 1
            if golden_crosses <= 5:  # 只显示前5次
                date = df_with_signals.iloc[i]['date']
                price = df_with_signals.iloc[i]['close']
                print(f"   金叉 #{golden_crosses}: {date} 价格={price:.2f} DIF={dif_curr:.4f} DEA={dea_curr:.4f}")

        if dif_prev >= dea_prev and dif_curr < dea_curr:
            death_crosses += 1

    print(f"\n   总计金叉次数: {golden_crosses}")
    print(f"   总计死叉次数: {death_crosses}")

    # 6. 检查最近的MACD状态
    print("\n5. 最近的MACD状态...")
    last_5 = df_with_signals.tail(5)
    print("\n   日期         收盘价    DIF      DEA      柱状图")
    print("   " + "-"*55)
    for idx, row in last_5.iterrows():
        print(f"   {str(row['date'])[:10]}  {row['close']:7.2f}  {row['macd_dif']:7.4f}  {row['macd_dea']:7.4f}  {row['macd_hist']:7.4f}")

    # 7. 总结
    print(f"\n{'='*60}")
    print("总结:")
    if golden_crosses == 0:
        print("  ⚠️  数据中没有金叉信号出现")
        print("  可能原因:")
        print("    - 时间周期太短")
        print("    - 股票一直处于下跌趋势")
        print("    - MACD参数不适合该股票")
    elif len(buy_signals) == 0 and golden_crosses > 0:
        print(f"  ⚠️  有{golden_crosses}次金叉，但都被过滤条件阻止了")
        print("  建议:")
        print("    - 检查过滤参数设置")
        print("    - 尝试使用默认参数")
    else:
        print(f"  ✓ 策略正常工作，产生了{len(buy_signals)}次买入信号")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    # 可以通过命令行参数指定股票
    symbol = sys.argv[1] if len(sys.argv) > 1 else '01810.HK'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 365

    with app.app_context():
        debug_macd_strategy(symbol, days)
