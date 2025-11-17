"""布林带突破策略."""

from typing import Dict, Any, List
import pandas as pd
from app.strategies.base import BaseStrategy
from app.strategies.registry import StrategyRegistry
from app.services.indicator_service import IndicatorService


@StrategyRegistry.register
class BollBreakoutStrategy(BaseStrategy):
    """布林带突破策略.

    价格突破下轨时买入（超卖反弹），
    价格突破上轨时卖出（超买回调）。
    """

    strategy_id = 'boll_breakout'
    name = '布林带突破'
    description = '价格突破下轨买入，突破上轨卖出'
    category = 'indicator'

    @classmethod
    def get_min_required_days(cls, params: Dict[str, Any] = None) -> int:
        """获取布林带策略所需的最小数据天数.

        Returns:
            布林带默认使用20日均线，最少需要30天数据（20 + 10天缓冲）
        """
        return 30

    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成交易信号.

        Args:
            df: 包含OHLCV数据的DataFrame
            params: 策略参数
                - timeframe: 时间周期

        Returns:
            添加了'signal'列的DataFrame (1=买入, -1=卖出, 0=持有)
        """
        df = df.copy()
        df['signal'] = 0

        # 确保BOLL列存在
        if 'boll_mid' not in df.columns:
            df = IndicatorService.calculate_boll(df)

        # 生成信号
        for i in range(1, len(df)):
            close_prev = df.iloc[i-1]['close']
            close_curr = df.iloc[i]['close']
            lower_prev = df.iloc[i-1]['boll_lower']
            upper_prev = df.iloc[i-1]['boll_upper']
            lower_curr = df.iloc[i]['boll_lower']
            upper_curr = df.iloc[i]['boll_upper']

            # 价格突破下轨：买入信号（超卖）
            if close_prev > lower_prev and close_curr <= lower_curr:
                df.iloc[i, df.columns.get_loc('signal')] = 1

            # 价格突破上轨：卖出信号（超买）
            elif close_prev < upper_prev and close_curr >= upper_curr:
                df.iloc[i, df.columns.get_loc('signal')] = -1

        return df

    def analyze_current_signal(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前布林带突破信号接近度.

        Args:
            df: 包含价格和布林带数据的DataFrame
            params: 策略参数

        Returns:
            包含分析结果的字典
        """
        if df.empty:
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "status": "no_data",
                "message": "无可用数据"
            }

        latest = df.iloc[-1]

        if 'boll_upper' not in latest.index or 'boll_lower' not in latest.index:
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "status": "no_data",
                "message": "缺少布林带数据"
            }

        price = latest['close']
        upper = latest['boll_upper']
        middle = latest.get('boll_middle', latest.get('boll_mid', 0))
        lower = latest['boll_lower']

        # 计算价格在布林带中的位置
        band_width = upper - lower
        distance_to_upper = upper - price
        distance_to_lower = price - lower

        distance_to_upper_pct = (distance_to_upper / price) * 100
        distance_to_lower_pct = (distance_to_lower / price) * 100

        # 判断位置
        if price > upper:
            status = "above_upper"
            current_state = f"价格{price:.2f}元，突破上轨{upper:.2f}元，处于超买状态"
            proximity = "very_close"
            suggestion = "价格已突破上轨，可能出现回调，注意卖出信号"
        elif price < lower:
            status = "below_lower"
            current_state = f"价格{price:.2f}元，跌破下轨{lower:.2f}元，处于超卖状态"
            proximity = "very_close"
            suggestion = "价格已跌破下轨，可能出现反弹，关注买入机会"
        elif distance_to_upper_pct < 2:
            status = "near_upper"
            current_state = f"价格{price:.2f}元，接近上轨{upper:.2f}元"
            proximity = "close"
            suggestion = f"距离上轨仅{distance_to_upper_pct:.1f}%（约{distance_to_upper:.2f}元），如果继续上涨突破上轨，可能形成超买卖出信号"
        elif distance_to_lower_pct < 2:
            status = "near_lower"
            current_state = f"价格{price:.2f}元，接近下轨{lower:.2f}元"
            proximity = "close"
            suggestion = f"距离下轨仅{distance_to_lower_pct:.1f}%（约{distance_to_lower:.2f}元），如果继续下跌触及下轨，可能形成超卖买入信号"
        elif price > middle:
            status = "above_middle"
            current_state = f"价格{price:.2f}元，在中轨{middle:.2f}元上方"
            proximity = "moderate"
            suggestion = f"价格在中轨上方运行，距上轨还有{distance_to_upper_pct:.1f}%空间"
        else:
            status = "below_middle"
            current_state = f"价格{price:.2f}元，在中轨{middle:.2f}元下方"
            proximity = "moderate"
            suggestion = f"价格在中轨下方运行，距下轨还有{distance_to_lower_pct:.1f}%空间"

        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "status": status,
            "proximity": proximity,
            "indicators": {
                "当前价": round(price, 2),
                "上轨": round(upper, 2),
                "中轨": round(middle, 2),
                "下轨": round(lower, 2),
                "带宽": round(band_width, 2)
            },
            "current_state": current_state,
            "proximity_description": f"距上轨{distance_to_upper_pct:.1f}%，距下轨{distance_to_lower_pct:.1f}%",
            "suggestion": suggestion
        }
