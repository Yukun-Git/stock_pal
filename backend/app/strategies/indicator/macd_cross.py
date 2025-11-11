"""MACD金叉策略 - 高级配置版本."""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from app.strategies.base import BaseStrategy
from app.strategies.registry import StrategyRegistry
from app.services.indicator_service import IndicatorService


@StrategyRegistry.register
class MACDCrossStrategy(BaseStrategy):
    """MACD金叉策略 - 支持多种过滤和确认机制.

    基础信号：DIF线上穿DEA线时买入（金叉），DIF线下穿DEA线时卖出（死叉）

    高级功能：
    - 0轴位置过滤
    - 第二次金叉检测
    - 背离分析
    - MACD柱状图确认
    - 均线趋势过滤
    - 固定比例止损
    """

    strategy_id = 'macd_cross'
    name = 'MACD金叉'
    description = 'DIF上穿DEA买入，下穿卖出（支持多种过滤条件）'
    category = 'indicator'

    @classmethod
    def get_parameters(cls) -> List[Dict[str, Any]]:
        """返回策略参数定义."""
        # 获取基类参数（timeframe）
        base_params = super().get_parameters()

        # 移除基类的 hold_periods 参数（MACD用死叉卖出，不需要固定持有周期）
        base_params = [p for p in base_params if p['name'] != 'hold_periods']

        # MACD特有参数
        custom_params = [
            # === 1. MACD指标参数 ===
            {
                'name': 'macd_fast',
                'label': 'MACD快线周期',
                'type': 'integer',
                'default': 12,
                'min': 5,
                'max': 30,
                'description': 'MACD快速EMA周期'
            },
            {
                'name': 'macd_slow',
                'label': 'MACD慢线周期',
                'type': 'integer',
                'default': 26,
                'min': 20,
                'max': 60,
                'description': 'MACD慢速EMA周期'
            },
            {
                'name': 'macd_signal',
                'label': 'MACD信号线周期',
                'type': 'integer',
                'default': 9,
                'min': 5,
                'max': 20,
                'description': 'MACD信号线(DEA)周期'
            },

            # === 2. 0轴位置过滤 ===
            {
                'name': 'zero_line_filter',
                'label': '0轴位置过滤',
                'type': 'select',
                'default': 'none',
                'options': [
                    {'value': 'none', 'label': '不过滤'},
                    {'value': 'above_only', 'label': '仅0轴以上金叉'},
                    {'value': 'below_only', 'label': '仅0轴以下金叉'},
                    {'value': 'near_only', 'label': '仅0轴附近金叉'}
                ],
                'description': '根据DIF与0轴的位置关系过滤信号'
            },
            {
                'name': 'zero_line_threshold',
                'label': '0轴附近阈值',
                'type': 'float',
                'default': 0.05,
                'min': 0.01,
                'max': 0.5,
                'description': '定义"0轴附近"的范围（DIF绝对值小于此值）'
            },

            # === 3. 第二次金叉过滤 ===
            {
                'name': 'second_cross_only',
                'label': '仅交易第二次金叉',
                'type': 'boolean',
                'default': False,
                'description': '只在回调后再次金叉时买入（趋势确认）'
            },
            {
                'name': 'cross_lookback',
                'label': '金叉回看周期',
                'type': 'integer',
                'default': 10,
                'min': 5,
                'max': 30,
                'description': '向前查找前一次金叉的周期数'
            },

            # === 4. 背离分析 ===
            {
                'name': 'use_divergence',
                'label': '启用背离分析',
                'type': 'boolean',
                'default': False,
                'description': '检测价格与MACD的背离，增强信号可靠性'
            },
            {
                'name': 'divergence_lookback',
                'label': '背离回看周期',
                'type': 'integer',
                'default': 20,
                'min': 10,
                'max': 50,
                'description': '寻找背离的回看周期数'
            },
            {
                'name': 'divergence_type',
                'label': '背离类型',
                'type': 'select',
                'default': 'both',
                'options': [
                    {'value': 'bullish', 'label': '仅底背离（买入增强）'},
                    {'value': 'bearish', 'label': '仅顶背离（卖出增强）'},
                    {'value': 'both', 'label': '底背离和顶背离'}
                ],
                'description': '使用哪种类型的背离信号'
            },

            # === 5. MACD柱状图确认 ===
            {
                'name': 'histogram_confirm',
                'label': '柱状图确认',
                'type': 'boolean',
                'default': False,
                'description': '要求金叉时MACD柱由负转正'
            },
            {
                'name': 'histogram_increasing',
                'label': '柱状图放大',
                'type': 'boolean',
                'default': False,
                'description': '要求柱状图连续放大（动能增强）'
            },

            # === 6. 均线趋势过滤 ===
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
                'name': 'trend_ma_position',
                'label': '价格与均线位置',
                'type': 'select',
                'default': 'above',
                'options': [
                    {'value': 'above', 'label': '价格在均线上方'},
                    {'value': 'below', 'label': '价格在均线下方'},
                    {'value': 'any', 'label': '不限'}
                ],
                'description': '买入时要求价格相对均线的位置'
            },

            # === 7. 固定止损 ===
            {
                'name': 'stop_loss_pct',
                'label': '固定止损比例',
                'type': 'float',
                'default': 0,
                'min': 0,
                'max': 0.2,
                'description': '买入后下跌超过此比例则止损（0=不启用）'
            }
        ]

        return base_params + custom_params

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
        macd_fast = params.get('macd_fast', 12)
        macd_slow = params.get('macd_slow', 26)
        macd_signal = params.get('macd_signal', 9)

        # 计算MACD指标
        df = self._calculate_macd(df, macd_fast, macd_slow, macd_signal)

        # 计算趋势过滤均线（如果启用）
        trend_ma_period = params.get('trend_ma_period', 0)
        if trend_ma_period > 0:
            df = IndicatorService.calculate_ma(df, [trend_ma_period])

        # 初始化买入价格列（用于止损）
        df['buy_price'] = np.nan
        current_position = False
        buy_price = 0

        # 逐行生成信号
        for i in range(1, len(df)):
            # === 检测基础金叉/死叉 ===
            dif_prev = df.iloc[i-1]['macd_dif']
            dea_prev = df.iloc[i-1]['macd_dea']
            dif_curr = df.iloc[i]['macd_dif']
            dea_curr = df.iloc[i]['macd_dea']

            is_golden_cross = dif_prev <= dea_prev and dif_curr > dea_curr
            is_death_cross = dif_prev >= dea_prev and dif_curr < dea_curr

            # === 买入信号处理 ===
            if is_golden_cross and not current_position:
                # 应用所有过滤条件
                if self._check_all_buy_filters(df, i, params):
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    current_position = True
                    buy_price = df.iloc[i]['close']
                    df.iloc[i, df.columns.get_loc('buy_price')] = buy_price

            # === 卖出信号处理 ===
            elif current_position:
                should_sell = False

                # 1. 检查固定止损
                stop_loss_pct = params.get('stop_loss_pct', 0)
                if stop_loss_pct > 0:
                    current_price = df.iloc[i]['close']
                    if current_price < buy_price * (1 - stop_loss_pct):
                        should_sell = True  # 止损卖出

                # 2. 检查死叉卖出
                if is_death_cross:
                    should_sell = True

                # 3. 检查顶背离卖出（如果启用）
                if params.get('use_divergence', False):
                    divergence_type = params.get('divergence_type', 'both')
                    if divergence_type in ['bearish', 'both']:
                        if self._detect_bearish_divergence(df, i, params):
                            should_sell = True

                if should_sell:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    current_position = False
                    buy_price = 0

        return df

    def _calculate_macd(self, df: pd.DataFrame, fast: int, slow: int, signal: int) -> pd.DataFrame:
        """计算MACD指标（支持自定义参数）.

        Args:
            df: 数据DataFrame
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            添加了MACD列的DataFrame
        """
        # 计算快慢EMA
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        # 计算DIF
        df['macd_dif'] = ema_fast - ema_slow

        # 计算DEA (信号线)
        df['macd_dea'] = df['macd_dif'].ewm(span=signal, adjust=False).mean()

        # 计算MACD柱
        df['macd_hist'] = (df['macd_dif'] - df['macd_dea']) * 2

        return df

    def _check_all_buy_filters(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """检查所有买入过滤条件.

        Args:
            df: 数据DataFrame
            i: 当前索引
            params: 策略参数

        Returns:
            是否通过所有过滤条件
        """
        # 1. 0轴位置过滤
        if not self._check_zero_line_filter(df, i, params):
            return False

        # 2. 第二次金叉检查
        if params.get('second_cross_only', False):
            if not self._check_second_cross(df, i, params):
                return False

        # 3. 背离分析
        if params.get('use_divergence', False):
            divergence_type = params.get('divergence_type', 'both')
            if divergence_type in ['bullish', 'both']:
                # 底背离增强买入信号，但不强制要求
                # 这里我们只是检测，不作为必要条件
                pass

        # 4. MACD柱状图确认
        if not self._check_histogram_confirm(df, i, params):
            return False

        # 5. 均线趋势过滤
        if not self._check_trend_filter(df, i, params):
            return False

        return True

    def _check_zero_line_filter(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """检查0轴位置过滤.

        Args:
            df: 数据DataFrame
            i: 当前索引
            params: 策略参数

        Returns:
            是否通过0轴过滤
        """
        zero_line_filter = params.get('zero_line_filter', 'none')
        if zero_line_filter == 'none':
            return True

        dif = df.iloc[i]['macd_dif']
        threshold = params.get('zero_line_threshold', 0.05)

        if zero_line_filter == 'above_only':
            return dif > 0
        elif zero_line_filter == 'below_only':
            return dif < 0
        elif zero_line_filter == 'near_only':
            return abs(dif) < threshold

        return True

    def _check_second_cross(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """检查是否为第二次金叉.

        Args:
            df: 数据DataFrame
            i: 当前索引
            params: 策略参数

        Returns:
            是否为第二次金叉
        """
        lookback = params.get('cross_lookback', 10)
        start = max(1, i - lookback)

        # 向前查找是否存在前一次金叉
        found_previous_cross = False
        found_death_cross_between = False

        for j in range(i - 1, start, -1):
            dif_prev = df.iloc[j-1]['macd_dif']
            dea_prev = df.iloc[j-1]['macd_dea']
            dif_curr = df.iloc[j]['macd_dif']
            dea_curr = df.iloc[j]['macd_dea']

            # 检查金叉
            if dif_prev <= dea_prev and dif_curr > dea_curr:
                found_previous_cross = True
                break

            # 检查死叉（确保中间有回调）
            if dif_prev >= dea_prev and dif_curr < dea_curr:
                found_death_cross_between = True

        # 第二次金叉 = 找到前一次金叉 且 中间有死叉
        return found_previous_cross

    def _detect_bullish_divergence(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """检测底背离（买入信号增强）.

        价格创新低但MACD不创新低，表示下跌动能减弱。

        Args:
            df: 数据DataFrame
            i: 当前索引
            params: 策略参数

        Returns:
            是否存在底背离
        """
        lookback = params.get('divergence_lookback', 20)
        start = max(0, i - lookback)

        current_price = df.iloc[i]['close']
        current_dif = df.iloc[i]['macd_dif']

        # 在回看周期内找最低价格和对应的DIF
        price_low = df.iloc[start:i]['close'].min()
        price_low_idx = df.iloc[start:i]['close'].idxmin()
        dif_at_price_low = df.loc[price_low_idx, 'macd_dif']

        # 底背离条件：当前价格创新低，但DIF没有创新低（甚至更高）
        if current_price <= price_low and current_dif > dif_at_price_low:
            return True

        return False

    def _detect_bearish_divergence(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """检测顶背离（卖出信号增强）.

        价格创新高但MACD不创新高，表示上涨动能减弱。

        Args:
            df: 数据DataFrame
            i: 当前索引
            params: 策略参数

        Returns:
            是否存在顶背离
        """
        lookback = params.get('divergence_lookback', 20)
        start = max(0, i - lookback)

        current_price = df.iloc[i]['close']
        current_dif = df.iloc[i]['macd_dif']

        # 在回看周期内找最高价格和对应的DIF
        price_high = df.iloc[start:i]['close'].max()
        price_high_idx = df.iloc[start:i]['close'].idxmax()
        dif_at_price_high = df.loc[price_high_idx, 'macd_dif']

        # 顶背离条件：当前价格创新高，但DIF没有创新高（甚至更低）
        if current_price >= price_high and current_dif < dif_at_price_high:
            return True

        return False

    def _check_histogram_confirm(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """检查MACD柱状图确认.

        Args:
            df: 数据DataFrame
            i: 当前索引
            params: 策略参数

        Returns:
            是否通过柱状图确认
        """
        if not params.get('histogram_confirm', False):
            return True

        hist_prev = df.iloc[i-1]['macd_hist']
        hist_curr = df.iloc[i]['macd_hist']

        # 要求柱由负转正
        if hist_prev >= 0 or hist_curr <= 0:
            return False

        # 如果还要求柱状图放大
        if params.get('histogram_increasing', False):
            if hist_curr <= hist_prev:
                return False

        return True

    def _check_trend_filter(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """检查均线趋势过滤.

        Args:
            df: 数据DataFrame
            i: 当前索引
            params: 策略参数

        Returns:
            是否通过趋势过滤
        """
        trend_ma_period = params.get('trend_ma_period', 0)
        if trend_ma_period == 0:
            return True

        ma_col = f'ma{trend_ma_period}'
        if ma_col not in df.columns:
            return True  # 如果均线不存在，跳过过滤

        current_price = df.iloc[i]['close']
        ma_value = df.iloc[i][ma_col]

        position = params.get('trend_ma_position', 'above')

        if position == 'above':
            return current_price > ma_value
        elif position == 'below':
            return current_price < ma_value
        else:  # 'any'
            return True

    def analyze_current_signal(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前MACD金叉信号接近度.

        Args:
            df: 包含价格和MACD数据的DataFrame
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
        prev = df.iloc[-2] if len(df) > 1 else None

        # 确保MACD列存在
        if 'macd_dif' not in latest.index or 'macd_dea' not in latest.index:
            return {
                "strategy_id": self.strategy_id,
                "strategy_name": self.name,
                "status": "no_data",
                "message": "缺少MACD数据"
            }

        dif = latest['macd_dif']
        dea = latest['macd_dea']
        hist = latest.get('macd_hist', (dif - dea) * 2)

        distance = dif - dea

        # 判断接近程度（基于柱状图高度）
        if abs(hist) < 0.05:
            proximity = "very_close"
            proximity_text = "非常接近"
        elif abs(hist) < 0.15:
            proximity = "close"
            proximity_text = "接近"
        elif abs(hist) < 0.3:
            proximity = "moderate"
            proximity_text = "中等距离"
        else:
            proximity = "far"
            proximity_text = "距离较远"

        # 判断当前状态和趋势
        if dif > dea:
            # DIF在上，多头
            status = "bullish"
            current_state = "MACD处于金叉状态，DIF线在DEA线上方"

            if hist > 0 and prev is not None and 'macd_hist' in prev.index:
                if hist < prev.get('macd_hist', 0):
                    trend = "但柱状图正在缩短，动能减弱"
                else:
                    trend = "且柱状图正在放大，动能增强"
            else:
                trend = ""

            suggestion = f"持有观望，如果DIF下穿DEA（柱状图转负），将产生死叉卖出信号{trend}"
        else:
            # DIF在下，空头
            status = "bearish"
            current_state = "MACD处于死叉状态，DIF线在DEA线下方"

            if hist < 0 and prev is not None and 'macd_hist' in prev.index:
                prev_hist = prev.get('macd_hist', 0)
                if abs(hist) < abs(prev_hist):
                    trend = "且柱状图正在缩短，下跌动能减弱"
                else:
                    trend = "且柱状图正在放大，下跌动能增强"
            else:
                trend = ""

            # 估算需要的价格变化
            if abs(distance) < 0.1:
                price_outlook = "如果明天股价上涨1-2%"
            elif abs(distance) < 0.3:
                price_outlook = "如果未来2-3天股价上涨3-5%"
            else:
                price_outlook = "需要持续上涨趋势"

            suggestion = f"{price_outlook}，DIF可能上穿DEA产生金叉买入信号{trend}"

        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "status": status,
            "proximity": proximity,
            "indicators": {
                "DIF": round(dif, 3),
                "DEA": round(dea, 3),
                "柱状图": round(hist, 3)
            },
            "current_state": current_state,
            "proximity_description": f"DIF与DEA线{proximity_text}（差距{abs(distance):.3f}）",
            "suggestion": suggestion
        }
