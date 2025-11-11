"""早晨之星策略."""

from typing import Dict, Any, List
import pandas as pd
from app.strategies.base import BaseStrategy
from app.strategies.registry import StrategyRegistry
from app.services.indicator_service import IndicatorService


@StrategyRegistry.register
class MorningStarStrategy(BaseStrategy):
    """早晨之星策略.

    底部反转K线形态策略，由三根连续K线组合而成。
    当检测到完整的早晨之星形态时买入，
    持有指定周期后卖出，或提前检测到暮星形态时卖出。
    """

    strategy_id = 'morning_star'
    name = '早晨之星'
    description = '底部反转形态，三根K线组合，看涨信号'
    category = 'pattern'

    @classmethod
    def get_parameters(cls) -> List[Dict[str, Any]]:
        """返回策略参数定义."""
        # 继承基类参数（timeframe和hold_periods）
        base_params = super().get_parameters()

        # 添加策略特有参数
        custom_params = [
            {
                'name': 'use_evening_star_exit',
                'label': '使用暮星退出',
                'type': 'boolean',
                'default': True,
                'description': '检测到暮星形态时提前退出'
            }
        ]

        return base_params + custom_params

    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成交易信号.

        Args:
            df: 包含OHLCV数据的DataFrame
            params: 策略参数
                - timeframe: 时间周期（'D'=日线, 'W'=周线）
                - hold_periods: 持有周期数
                - use_evening_star_exit: 是否使用暮星形态提前退出

        Returns:
            添加了'signal'列的DataFrame (1=买入, -1=卖出, 0=持有)
        """
        df = df.copy()
        df['signal'] = 0

        # 获取参数
        hold_periods = params.get('hold_periods', 5)
        use_evening_star = params.get('use_evening_star_exit', True)

        # 买入信号：检测早晨之星形态
        for i in range(2, len(df)):
            if IndicatorService.detect_morning_star(df, i):
                df.loc[df.index[i], 'signal'] = 1

        # 卖出信号
        buy_indices = df[df['signal'] == 1].index.tolist()
        for buy_idx in buy_indices:
            # 计算持有期满的卖出位置
            buy_position = df.index.get_loc(buy_idx)
            sell_position = min(buy_position + hold_periods, len(df) - 1)
            sell_idx = df.index[sell_position]
            df.loc[sell_idx, 'signal'] = -1

        # 可选：暮星形态提前退出
        if use_evening_star:
            for i in range(2, len(df)):
                if IndicatorService.detect_evening_star(df, i):
                    # 只有在持仓期间检测到暮星才卖出
                    # 简化处理：直接标记为卖出信号
                    df.loc[df.index[i], 'signal'] = -1

        return df

    def analyze_current_signal(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前早晨之星形态信号接近度.

        Args:
            df: 包含价格数据的DataFrame
            params: 策略参数

        Returns:
            包含分析结果的字典
        """
        if df.empty or len(df) < 3:
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "status": "no_data",
                "message": "数据不足，至少需要3根K线"
            }

        latest = df.iloc[-1]
        prev1 = df.iloc[-2]
        prev2 = df.iloc[-3]

        # 检查是否刚好形成早晨之星
        if IndicatorService.detect_morning_star(df, len(df) - 1):
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "status": "signal_triggered",
                "proximity": "very_close",
                "indicators": {
                    "最新收盘": round(latest['close'], 2),
                    "涨跌幅": f"{((latest['close'] - prev1['close']) / prev1['close'] * 100):+.2f}%"
                },
                "current_state": "✓ 检测到完整的早晨之星形态！",
                "proximity_description": "已形成买入信号",
                "suggestion": "当前已形成标准的早晨之星底部反转形态，建议考虑买入"
            }

        # 检查是否可能形成早晨之星（处于形成过程中）
        # 分析最近三根K线的特征
        close_2 = prev2['close']
        open_2 = prev2['open']
        close_1 = prev1['close']
        open_1 = prev1['open']
        close_0 = latest['close']
        open_0 = latest['open']

        # 第一根K线应该是阴线（收盘 < 开盘）
        is_first_bearish = close_2 < open_2
        # 第二根K线应该是小实体（可以是十字星或小阴阳线）
        body_1 = abs(close_1 - open_1)
        avg_body = (abs(prev2['close'] - prev2['open']) + abs(latest['close'] - latest['open'])) / 2
        is_second_small = body_1 < avg_body * 0.5
        # 第三根K线应该是阳线（收盘 > 开盘）
        is_third_bullish = close_0 > open_0

        # 判断形态接近程度
        if is_first_bearish and is_second_small:
            # 前两根已经符合，等待第三根确认
            status = "forming"
            proximity = "close"
            current_state = "前两根K线符合早晨之星特征（阴线+小实体），等待今日收盘确认"

            if is_third_bullish:
                # 第三根也是阳线，可能形成
                price_penetration = close_0 - close_2
                if price_penetration > 0:
                    suggestion = f"今日收阳线，有望形成早晨之星。如果收盘价持续高于前天收盘价{close_2:.2f}元，形态将确认"
                else:
                    suggestion = "今日虽收阳线，但力度不足，需要收盘价进一步上涨才能确认早晨之星形态"
            else:
                suggestion = "今日收阴线，早晨之星形态尚未确认，需等待明日是否收出强势阳线"

        elif is_first_bearish:
            # 只有第一根符合
            status = "potential"
            proximity = "moderate"
            current_state = "昨日收阴线，观察今日是否形成小实体K线"
            suggestion = "如果今日形成十字星或小实体K线，并且明日收出阳线，可能形成早晨之星底部反转"

        else:
            # 不符合早晨之星特征
            status = "neutral"
            proximity = "far"

            # 检查是否在下跌趋势中（早晨之星的前提条件）
            if close_0 < close_1 and close_1 < close_2:
                current_state = "当前处于下跌趋势，但尚未形成早晨之星形态"
                suggestion = "继续观察，如果后续出现阴线+小实体+阳线的组合，可能形成早晨之星买入机会"
            else:
                current_state = "当前K线走势不符合早晨之星形态特征"
                suggestion = "早晨之星需要在下跌趋势中形成，当前暂无明确信号"

        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "status": status,
            "proximity": proximity,
            "indicators": {
                "最新收盘": round(latest['close'], 2),
                "昨日收盘": round(prev1['close'], 2),
                "前日收盘": round(prev2['close'], 2)
            },
            "current_state": current_state,
            "proximity_description": f"形态完成度: {['低', '中', '高'][['far', 'moderate', 'close'].index(proximity) if proximity in ['far', 'moderate', 'close'] else 0]}",
            "suggestion": suggestion
        }
