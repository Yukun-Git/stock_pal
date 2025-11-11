"""KDJ金叉策略."""

from typing import Dict, Any, List
import pandas as pd
from app.strategies.base import BaseStrategy
from app.strategies.registry import StrategyRegistry
from app.services.indicator_service import IndicatorService


@StrategyRegistry.register
class KDJCrossStrategy(BaseStrategy):
    """KDJ金叉策略.

    K线上穿D线且在低位(超卖区)买入，
    K线在高位(超买区)卖出。
    """

    strategy_id = 'kdj_cross'
    name = 'KDJ金叉'
    description = 'K线上穿D线且在低位(< 30)买入，高位(> 70)卖出'
    category = 'indicator'

    @classmethod
    def get_parameters(cls) -> List[Dict[str, Any]]:
        """返回策略参数定义."""
        base_params = super().get_parameters()

        custom_params = [
            {
                'name': 'oversold',
                'label': '超卖阈值',
                'type': 'integer',
                'default': 30,
                'min': 10,
                'max': 40,
                'description': 'KDJ低于此值视为超卖区域'
            },
            {
                'name': 'overbought',
                'label': '超买阈值',
                'type': 'integer',
                'default': 70,
                'min': 60,
                'max': 90,
                'description': 'KDJ高于此值视为超买区域'
            }
        ]

        return base_params + custom_params

    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成交易信号.

        Args:
            df: 包含OHLCV数据的DataFrame
            params: 策略参数
                - timeframe: 时间周期
                - oversold: 超卖阈值
                - overbought: 超买阈值

        Returns:
            添加了'signal'列的DataFrame (1=买入, -1=卖出, 0=持有)
        """
        df = df.copy()
        df['signal'] = 0

        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        # 确保KDJ列存在
        if 'kdj_k' not in df.columns:
            df = IndicatorService.calculate_kdj(df)

        # 生成信号
        for i in range(1, len(df)):
            k_prev = df.iloc[i-1]['kdj_k']
            d_prev = df.iloc[i-1]['kdj_d']
            k_curr = df.iloc[i]['kdj_k']
            d_curr = df.iloc[i]['kdj_d']

            # KDJ金叉且在超卖区：买入信号
            if k_prev <= d_prev and k_curr > d_curr and k_curr < oversold:
                df.iloc[i, df.columns.get_loc('signal')] = 1

            # KDJ在超买区：卖出信号
            elif k_curr > overbought:
                df.iloc[i, df.columns.get_loc('signal')] = -1

        return df

    def analyze_current_signal(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前KDJ金叉信号接近度.

        Args:
            df: 包含价格和KDJ数据的DataFrame
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

        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        latest = df.iloc[-1]

        if 'kdj_k' not in latest.index or 'kdj_d' not in latest.index:
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "status": "no_data",
                "message": "缺少KDJ数据"
            }

        k = latest['kdj_k']
        d = latest['kdj_d']
        j = latest.get('kdj_j', 3 * k - 2 * d)

        distance = k - d

        # 判断接近程度
        if abs(distance) < 2:
            proximity = "very_close"
            proximity_text = "非常接近"
        elif abs(distance) < 5:
            proximity = "close"
            proximity_text = "接近"
        elif abs(distance) < 10:
            proximity = "moderate"
            proximity_text = "中等距离"
        else:
            proximity = "far"
            proximity_text = "距离较远"

        # 判断区域
        if k < 20:
            zone = "超卖区"
            zone_description = "KDJ在超卖区"
        elif k > 80:
            zone = "超买区"
            zone_description = "KDJ在超买区"
        else:
            zone = "正常区"
            zone_description = "KDJ在正常区域"

        # 判断金叉/死叉状态
        if k > d:
            status = "bullish"
            current_state = f"K线在D线上方（金叉状态），{zone_description}"

            if k > 80:
                suggestion = f"KDJ处于超买区的金叉状态，如果K线下穿D线，将产生死叉卖出信号"
            else:
                suggestion = f"保持金叉状态，继续持有观望"
        else:
            status = "bearish"
            current_state = f"K线在D线下方（死叉状态），{zone_description}"

            if k < 20:
                if abs(distance) < 5:
                    suggestion = f"KDJ在超卖区且K、D线{proximity_text}，如果未来1-2天股价反弹，K线可能上穿D线产生金叉买入信号"
                else:
                    suggestion = f"KDJ在超卖区死叉状态，等待K线上穿D线形成金叉买入信号"
            else:
                suggestion = f"观望中，如果K线上穿D线将产生金叉买入信号"

        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "status": status,
            "proximity": proximity,
            "indicators": {
                "K": round(k, 1),
                "D": round(d, 1),
                "J": round(j, 1)
            },
            "current_state": current_state,
            "proximity_description": f"K线与D线{proximity_text}（差距{abs(distance):.1f}）",
            "suggestion": suggestion
        }
