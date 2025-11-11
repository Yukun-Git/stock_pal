"""RSI反转策略."""

from typing import Dict, Any, List
import pandas as pd
from app.strategies.base import BaseStrategy
from app.strategies.registry import StrategyRegistry
from app.services.indicator_service import IndicatorService


@StrategyRegistry.register
class RSIReversalStrategy(BaseStrategy):
    """RSI反转策略.

    RSI低于超卖阈值后反弹时买入，
    RSI高于超买阈值后回落时卖出。
    """

    strategy_id = 'rsi_reversal'
    name = 'RSI反转'
    description = 'RSI < 30超卖买入，RSI > 70超买卖出'
    category = 'indicator'

    @classmethod
    def get_parameters(cls) -> List[Dict[str, Any]]:
        """返回策略参数定义."""
        base_params = super().get_parameters()

        custom_params = [
            {
                'name': 'period',
                'label': 'RSI周期',
                'type': 'integer',
                'default': 6,
                'min': 2,
                'max': 30,
                'description': 'RSI指标的计算周期'
            },
            {
                'name': 'oversold',
                'label': '超卖阈值',
                'type': 'integer',
                'default': 30,
                'min': 10,
                'max': 40,
                'description': 'RSI低于此值视为超卖'
            },
            {
                'name': 'overbought',
                'label': '超买阈值',
                'type': 'integer',
                'default': 70,
                'min': 60,
                'max': 90,
                'description': 'RSI高于此值视为超买'
            }
        ]

        return base_params + custom_params

    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成交易信号.

        Args:
            df: 包含OHLCV数据的DataFrame
            params: 策略参数
                - timeframe: 时间周期
                - period: RSI周期
                - oversold: 超卖阈值
                - overbought: 超买阈值

        Returns:
            添加了'signal'列的DataFrame (1=买入, -1=卖出, 0=持有)
        """
        df = df.copy()
        df['signal'] = 0

        period = params.get('period', 6)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        # 确保RSI列存在
        if f'rsi{period}' not in df.columns:
            df = IndicatorService.calculate_rsi(df, [period])

        rsi_col = f'rsi{period}'

        # 生成信号
        for i in range(1, len(df)):
            rsi_prev = df.iloc[i-1][rsi_col]
            rsi_curr = df.iloc[i][rsi_col]

            # RSI上穿超卖线：买入信号
            if rsi_prev < oversold and rsi_curr >= oversold:
                df.iloc[i, df.columns.get_loc('signal')] = 1

            # RSI下穿超买线：卖出信号
            elif rsi_prev > overbought and rsi_curr <= overbought:
                df.iloc[i, df.columns.get_loc('signal')] = -1

        return df

    def analyze_current_signal(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前RSI反转信号接近度.

        Args:
            df: 包含价格和RSI数据的DataFrame
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

        period = params.get('period', 6)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        rsi_col = f'rsi{period}'
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else None

        if rsi_col not in latest.index:
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "status": "no_data",
                "message": "缺少RSI数据"
            }

        rsi = latest[rsi_col]

        # 判断当前区域
        if rsi < oversold:
            status = "oversold"
            zone = "超卖区"
            current_state = f"RSI={rsi:.1f}，处于超卖区（<{oversold}），市场可能反弹"

            distance_to_signal = oversold - rsi
            if distance_to_signal < 0:
                suggestion = f"RSI正在从超卖区反弹，如果继续上升突破{oversold}，将产生买入信号"
                proximity = "very_close"
            else:
                suggestion = f"RSI仍在超卖区，暂无买入信号。继续关注反弹机会"
                proximity = "moderate"

        elif rsi > overbought:
            status = "overbought"
            zone = "超买区"
            current_state = f"RSI={rsi:.1f}，处于超买区（>{overbought}），市场可能回调"

            distance_to_signal = rsi - overbought
            if prev is not None and rsi_col in prev.index:
                prev_rsi = prev[rsi_col]
                if rsi < prev_rsi:
                    suggestion = f"RSI正在从超买区回落，如果继续下降跌破{overbought}，将产生卖出信号"
                    proximity = "very_close"
                else:
                    suggestion = f"RSI仍在超买区上升，暂时持有，注意回落风险"
                    proximity = "close"
            else:
                suggestion = f"RSI处于超买区，关注回调机会"
                proximity = "close"

        elif rsi >= oversold and rsi <= 50:
            status = "neutral_low"
            zone = "中性偏低区"
            distance_to_oversold = rsi - oversold
            current_state = f"RSI={rsi:.1f}，处于中性偏低区域"

            if distance_to_oversold < 5:
                proximity = "close"
                suggestion = f"距离超卖区仅差{distance_to_oversold:.1f}点，如果股价继续下跌，可能进入超卖区形成买入机会"
            else:
                proximity = "moderate"
                suggestion = f"RSI在正常范围内，等待进入超卖区（<{oversold}）后反弹买入"

        elif rsi > 50 and rsi <= overbought:
            status = "neutral_high"
            zone = "中性偏高区"
            distance_to_overbought = overbought - rsi
            current_state = f"RSI={rsi:.1f}，处于中性偏高区域"

            if distance_to_overbought < 5:
                proximity = "close"
                suggestion = f"距离超买区仅差{distance_to_overbought:.1f}点，如果股价继续上涨，可能进入超买区形成卖出机会"
            else:
                proximity = "moderate"
                suggestion = f"RSI在正常范围内，等待进入超买区（>{overbought}）后回落卖出"
        else:
            status = "neutral"
            zone = "中性区"
            current_state = f"RSI={rsi:.1f}，处于中性区域"
            proximity = "far"
            suggestion = "RSI在正常范围内，暂无明确信号"

        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "status": status,
            "proximity": proximity,
            "indicators": {
                f"RSI{period}": round(rsi, 1),
                "超卖线": oversold,
                "超买线": overbought
            },
            "current_state": current_state,
            "proximity_description": f"RSI当前在{zone}",
            "suggestion": suggestion
        }
