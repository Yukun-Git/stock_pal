"""简化的MACD调试脚本 - 直接使用yfinance"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    # 计算快慢EMA
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()

    # 计算DIF
    df['macd_dif'] = ema_fast - ema_slow

    # 计算DEA (信号线)
    df['macd_dea'] = df['macd_dif'].ewm(span=signal, adjust=False).mean()

    # 计算MACD柱
    df['macd_hist'] = (df['macd_dif'] - df['macd_dea']) * 2

    return df

def analyze_macd(symbol='1810.HK', days=365):
    """分析MACD金叉信号"""

    print(f"\n{'='*60}")
    print(f"MACD策略分析 - {symbol}")
    print(f"{'='*60}\n")

    # 1. 获取数据
    print("1. 获取历史数据...")
    try:
        end = datetime.now()
        start = end - timedelta(days=days)

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, auto_adjust=True)

        if df.empty:
            print(f"   ✗ 未获取到数据")
            return

        print(f"   ✓ 成功获取 {len(df)} 条数据")
        print(f"   日期范围: {df.index[0]} 到 {df.index[-1]}")
        print(f"   最新收盘价: {df['Close'].iloc[-1]:.2f}")

    except Exception as e:
        print(f"   ✗ 获取数据失败: {e}")
        return

    # 2. 计算MACD
    print("\n2. 计算MACD指标...")
    df = calculate_macd(df)
    print(f"   ✓ MACD计算完成")

    # 3. 检测金叉/死叉
    print("\n3. 分析MACD金叉/死叉...")

    golden_crosses = []
    death_crosses = []

    for i in range(1, len(df)):
        dif_prev = df['macd_dif'].iloc[i-1]
        dea_prev = df['macd_dea'].iloc[i-1]
        dif_curr = df['macd_dif'].iloc[i]
        dea_curr = df['macd_dea'].iloc[i]

        # 金叉
        if dif_prev <= dea_prev and dif_curr > dea_curr:
            golden_crosses.append({
                'date': df.index[i],
                'price': df['Close'].iloc[i],
                'dif': dif_curr,
                'dea': dea_curr
            })

        # 死叉
        if dif_prev >= dea_prev and dif_curr < dea_curr:
            death_crosses.append({
                'date': df.index[i],
                'price': df['Close'].iloc[i],
                'dif': dif_curr,
                'dea': dea_curr
            })

    print(f"   总计金叉次数: {len(golden_crosses)}")
    print(f"   总计死叉次数: {len(death_crosses)}")

    if len(golden_crosses) > 0:
        print(f"\n   前5次金叉详情:")
        for i, cross in enumerate(golden_crosses[:5], 1):
            print(f"   金叉 #{i}: {str(cross['date'])[:10]} "
                  f"价格={cross['price']:.2f} "
                  f"DIF={cross['dif']:.4f} DEA={cross['dea']:.4f}")
    else:
        print(f"\n   ⚠️  数据中没有金叉信号！")

    # 4. 显示最近的MACD状态
    print("\n4. 最近5天的MACD状态...")
    print("\n   日期         收盘价    DIF      DEA      柱状图")
    print("   " + "-"*55)

    last_5 = df.tail(5)
    for idx in range(len(last_5)):
        row = last_5.iloc[idx]
        date = str(last_5.index[idx])[:10]
        print(f"   {date}  {row['Close']:7.2f}  "
              f"{row['macd_dif']:7.4f}  {row['macd_dea']:7.4f}  "
              f"{row['macd_hist']:7.4f}")

    # 5. 总结
    print(f"\n{'='*60}")
    print("总结:")
    if len(golden_crosses) == 0:
        print("  ⚠️  过去一年没有MACD金叉信号")
        print("  可能原因:")
        print("    - 股票一直处于下跌或横盘状态")
        print("    - MACD参数(12,26,9)不适合该股票的波动特性")
        print("  ")
        print("  建议:")
        print("    - 尝试更敏感的参数，如 (8, 17, 9)")
        print("    - 尝试其他策略，如RSI、布林带等")
        print("    - 选择波动较大的股票测试")
    else:
        print(f"  ✓ 检测到 {len(golden_crosses)} 次金叉信号")
        print(f"  ✓ 检测到 {len(death_crosses)} 次死叉信号")
        print(f"  ")
        if len(golden_crosses) < 3:
            print(f"  建议: 信号较少，可以尝试更敏感的参数")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    symbol = sys.argv[1] if len(sys.argv) > 1 else '1810.HK'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 365

    analyze_macd(symbol, days)
