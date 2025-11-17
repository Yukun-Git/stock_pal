"""均线金叉策略."""

from typing import Dict, Any, List
import pandas as pd
from app.strategies.base import BaseStrategy
from app.strategies.registry import StrategyRegistry
from app.services.indicator_service import IndicatorService


@StrategyRegistry.register
class MACrossStrategy(BaseStrategy):
    """均线金叉策略.

    短期均线上穿长期均线时买入（金叉），
    短期均线下穿长期均线时卖出（死叉）。
    """

    strategy_id = 'ma_cross'
    name = '均线金叉'
    description = '短期均线上穿长期均线买入，下穿卖出'
    category = 'indicator'

    @classmethod
    def get_parameters(cls) -> List[Dict[str, Any]]:
        """返回策略参数定义."""
        # 获取基类参数
        base_params = super().get_parameters()

        # 添加MA特有参数
        custom_params = [
            {
                'name': 'fast_period',
                'label': '快速周期',
                'type': 'integer',
                'default': 5,
                'min': 2,
                'max': 60,
                'description': '短期移动平均线的周期'
            },
            {
                'name': 'slow_period',
                'label': '慢速周期',
                'type': 'integer',
                'default': 20,
                'min': 5,
                'max': 250,
                'description': '长期移动平均线的周期'
            }
        ]

        return base_params + custom_params

    @classmethod
    def get_min_required_days(cls, params: Dict[str, Any] = None) -> int:
        """获取MA策略所需的最小数据天数.

        Args:
            params: 策略参数，包含 slow_period

        Returns:
            最小所需数据天数 = 慢速均线周期 + 10天缓冲
        """
        if params is None:
            params = {}

        slow_period = params.get('slow_period', 20)
        return slow_period + 10

    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成交易信号.

        Args:
            df: 包含OHLCV数据的DataFrame
            params: 策略参数
                - timeframe: 时间周期
                - fast_period: 快速均线周期
                - slow_period: 慢速均线周期

        Returns:
            添加了'signal'列的DataFrame (1=买入, -1=卖出, 0=持有)
        """
        df = df.copy()
        df['signal'] = 0

        fast_period = params.get('fast_period', 5)
        slow_period = params.get('slow_period', 20)

        # 确保MA列存在
        if f'ma{fast_period}' not in df.columns:
            df = IndicatorService.calculate_ma(df, [fast_period, slow_period])

        # 生成信号
        for i in range(1, len(df)):
            fast_prev = df.iloc[i-1][f'ma{fast_period}']
            slow_prev = df.iloc[i-1][f'ma{slow_period}']
            fast_curr = df.iloc[i][f'ma{fast_period}']
            slow_curr = df.iloc[i][f'ma{slow_period}']

            # 金叉：买入信号
            if fast_prev <= slow_prev and fast_curr > slow_curr:
                df.iloc[i, df.columns.get_loc('signal')] = 1

            # 死叉：卖出信号
            elif fast_prev >= slow_prev and fast_curr < slow_curr:
                df.iloc[i, df.columns.get_loc('signal')] = -1

        return df

    def analyze_current_signal(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前均线金叉信号接近度.

        Args:
            df: 包含价格和均线数据的DataFrame
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

        fast_period = params.get('fast_period', 5)
        slow_period = params.get('slow_period', 20)

        fast_col = f'ma{fast_period}'
        slow_col = f'ma{slow_period}'

        # 获取最新数据
        latest = df.iloc[-1]

        if fast_col not in latest.index or slow_col not in latest.index:
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "status": "no_data",
                "message": "缺少均线数据"
            }

        fast_ma = latest[fast_col]
        slow_ma = latest[slow_col]
        distance = fast_ma - slow_ma
        distance_pct = (distance / slow_ma) * 100

        # 判断接近程度
        if abs(distance_pct) < 0.5:
            proximity = "very_close"
            proximity_text = "非常接近"
        elif abs(distance_pct) < 1.5:
            proximity = "close"
            proximity_text = "接近"
        elif abs(distance_pct) < 3:
            proximity = "moderate"
            proximity_text = "中等距离"
        else:
            proximity = "far"
            proximity_text = "距离较远"

        # 判断趋势和信号方向
        if distance > 0:
            # 快线在上，多头排列
            status = "bullish"
            current_state = f"短期均线({fast_period}日)在长期均线({slow_period}日)上方，多头排列"

            # 计算需要下跌多少才会死叉
            price_change_needed = abs(distance)
            price_change_pct = abs(distance_pct)

            suggestion = f"如果未来{fast_period}天股价下跌约{price_change_pct:.1f}%（至{latest['close']*(1-distance_pct/100):.2f}元附近），可能触发死叉卖出信号"
        else:
            # 快线在下，空头排列
            status = "bearish"
            current_state = f"短期均线({fast_period}日)在长期均线({slow_period}日)下方，空头排列"

            # 计算需要上涨多少才会金叉
            price_change_needed = abs(distance)
            price_change_pct = abs(distance_pct)

            suggestion = f"如果未来{fast_period}天股价上涨约{price_change_pct:.1f}%（至{latest['close']*(1+distance_pct/100):.2f}元附近），可能触发金叉买入信号"

        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "status": status,
            "proximity": proximity,
            "indicators": {
                f"MA{fast_period}": round(fast_ma, 2),
                f"MA{slow_period}": round(slow_ma, 2),
                "差距": f"{distance_pct:+.2f}%"
            },
            "current_state": current_state,
            "proximity_description": f"两条均线{proximity_text}（差距{abs(distance_pct):.2f}%）",
            "suggestion": suggestion
        }
