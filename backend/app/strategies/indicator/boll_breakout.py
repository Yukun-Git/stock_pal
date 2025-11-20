"""布林带突破策略 - 高级配置版本."""

from typing import Dict, Any, List
import pandas as pd
from app.strategies.base import BaseStrategy
from app.strategies.registry import StrategyRegistry
from app.services.indicator_service import IndicatorService


@StrategyRegistry.register
class BollBreakoutStrategy(BaseStrategy):
    """布林带突破策略 - 支持均值回归和突破跟随两种模式.

    均值回归模式（默认）：
    - 价格触及下轨买入（超卖反弹）
    - 价格触及上轨卖出（超买回调）
    - 适合震荡市

    突破跟随模式：
    - 价格突破上轨买入（趋势加强）
    - 价格跌破下轨卖出（趋势转弱）
    - 适合趋势市
    """

    strategy_id = 'boll_breakout'
    name = '布林带突破'
    description = '价格触及/突破布林带轨道时交易'
    category = 'indicator'

    @classmethod
    def get_parameters(cls) -> List[Dict[str, Any]]:
        """返回策略参数定义."""
        # 获取基类参数（timeframe）
        base_params = super().get_parameters()

        # 移除基类的 hold_periods 参数（布林带用轨道信号卖出）
        base_params = [p for p in base_params if p['name'] != 'hold_periods']

        # 布林带特有参数
        custom_params = [
            # === 1. 布林带计算参数 ===
            {
                'name': 'period',
                'label': '布林带周期',
                'type': 'integer',
                'default': 20,
                'min': 10,
                'max': 60,
                'description': '布林带中轨（移动平均线）的周期'
            },
            {
                'name': 'std_dev',
                'label': '标准差倍数',
                'type': 'float',
                'default': 2.0,
                'min': 1.0,
                'max': 3.0,
                'description': '上下轨距离中轨的标准差倍数（越大带宽越宽）'
            },

            # === 2. 策略类型 ===
            {
                'name': 'strategy_type',
                'label': '策略类型',
                'type': 'select',
                'default': 'mean_reversion',
                'options': [
                    {'value': 'mean_reversion', 'label': '均值回归（触及下轨买入，触及上轨卖出）'},
                    {'value': 'breakout', 'label': '突破跟随（突破上轨买入，跌破下轨卖出）'}
                ],
                'description': '选择策略逻辑：均值回归适合震荡市，突破跟随适合趋势市'
            },

            # === 3. 趋势过滤 ===
            {
                'name': 'trend_ma_period',
                'label': '趋势过滤均线周期',
                'type': 'integer',
                'default': 0,
                'min': 0,
                'max': 250,
                'description': '使用均线过滤趋势（0=不启用，推荐200）'
            },
            {
                'name': 'trend_position',
                'label': '价格与均线位置',
                'type': 'select',
                'default': 'above',
                'options': [
                    {'value': 'above', 'label': '价格在均线上方'},
                    {'value': 'below', 'label': '价格在均线下方'},
                    {'value': 'any', 'label': '不限'}
                ],
                'description': '买入时要求价格相对均线的位置'
            }
        ]

        return base_params + custom_params

    @classmethod
    def get_min_required_days(cls, params: Dict[str, Any] = None) -> int:
        """获取布林带策略所需的最小数据天数.

        Args:
            params: 策略参数，包含 period

        Returns:
            最小所需数据天数 = 布林带周期 + 10天缓冲
        """
        if params is None:
            params = {}

        period = params.get('period', 20)
        trend_ma_period = params.get('trend_ma_period', 0)

        # 取更大的周期，再加缓冲
        max_period = max(period, trend_ma_period)
        return max_period + 10

    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成交易信号.

        Args:
            df: 包含OHLCV数据的DataFrame
            params: 策略参数

        Returns:
            添加了'signal'列的DataFrame (1=买入, -1=卖出, 0=持有)
        """
        df = df.copy()
        df['signal'] = 0

        # 获取参数
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)
        strategy_type = params.get('strategy_type', 'mean_reversion')
        trend_ma_period = params.get('trend_ma_period', 0)

        # 计算布林带指标（使用自定义参数）
        df = IndicatorService.calculate_boll(df, period=period, std=std_dev)

        # 计算趋势过滤均线（如果启用）
        if trend_ma_period > 0:
            df = IndicatorService.calculate_ma(df, [trend_ma_period])

        # 根据策略类型生成信号
        if strategy_type == 'mean_reversion':
            df = self._generate_mean_reversion_signals(df, params)
        elif strategy_type == 'breakout':
            df = self._generate_breakout_signals(df, params)
        else:
            # 默认使用均值回归
            df = self._generate_mean_reversion_signals(df, params)

        return df

    def _generate_mean_reversion_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成均值回归信号（触及下轨买入，触及上轨卖出）.

        Args:
            df: 包含价格和布林带数据的DataFrame
            params: 策略参数

        Returns:
            添加了'signal'列的DataFrame
        """
        # 生成信号
        for i in range(1, len(df)):
            close_prev = df.iloc[i-1]['close']
            close_curr = df.iloc[i]['close']
            lower_prev = df.iloc[i-1]['boll_lower']
            upper_prev = df.iloc[i-1]['boll_upper']
            lower_curr = df.iloc[i]['boll_lower']
            upper_curr = df.iloc[i]['boll_upper']

            # 价格触及下轨：买入信号（超卖反弹）
            if close_prev > lower_prev and close_curr <= lower_curr:
                # 应用趋势过滤
                if self._check_trend_filter(df, i, params, is_buy=True):
                    df.iloc[i, df.columns.get_loc('signal')] = 1

            # 价格触及上轨：卖出信号（超买回调）
            elif close_prev < upper_prev and close_curr >= upper_curr:
                df.iloc[i, df.columns.get_loc('signal')] = -1

        return df

    def _generate_breakout_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成突破跟随信号（突破上轨买入，跌破下轨卖出）.

        Args:
            df: 包含价格和布林带数据的DataFrame
            params: 策略参数

        Returns:
            添加了'signal'列的DataFrame
        """
        # 生成信号
        for i in range(1, len(df)):
            close_prev = df.iloc[i-1]['close']
            close_curr = df.iloc[i]['close']
            lower_prev = df.iloc[i-1]['boll_lower']
            upper_prev = df.iloc[i-1]['boll_upper']
            lower_curr = df.iloc[i]['boll_lower']
            upper_curr = df.iloc[i]['boll_upper']

            # 价格突破上轨：买入信号（趋势加强）
            if close_prev < upper_prev and close_curr >= upper_curr:
                # 应用趋势过滤
                if self._check_trend_filter(df, i, params, is_buy=True):
                    df.iloc[i, df.columns.get_loc('signal')] = 1

            # 价格跌破下轨：卖出信号（趋势转弱）
            elif close_prev > lower_prev and close_curr <= lower_curr:
                df.iloc[i, df.columns.get_loc('signal')] = -1

        return df

    def _check_trend_filter(self, df: pd.DataFrame, i: int, params: Dict[str, Any], is_buy: bool = True) -> bool:
        """检查趋势过滤条件.

        Args:
            df: 数据DataFrame
            i: 当前索引
            params: 策略参数
            is_buy: 是否为买入信号

        Returns:
            是否通过趋势过滤
        """
        trend_ma_period = params.get('trend_ma_period', 0)
        if trend_ma_period == 0:
            return True  # 未启用趋势过滤

        ma_col = f'ma{trend_ma_period}'
        if ma_col not in df.columns:
            return True  # 如果均线不存在，跳过过滤

        current_price = df.iloc[i]['close']
        ma_value = df.iloc[i][ma_col]

        # 只对买入信号应用趋势过滤
        if not is_buy:
            return True

        trend_position = params.get('trend_position', 'above')

        if trend_position == 'above':
            return current_price > ma_value
        elif trend_position == 'below':
            return current_price < ma_value
        else:  # 'any'
            return True

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
