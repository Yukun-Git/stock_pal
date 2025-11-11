"""信号接近度分析服务 - 重构版本.

本服务使用策略模式，通过调用每个策略的 analyze_current_signal 方法
来进行信号分析，消除了原有的硬编码 if-elif 链。
"""

from typing import Dict, Any, List
import pandas as pd
from app.strategies.registry import StrategyRegistry


class SignalAnalysisService:
    """分析当前股票是否接近买入/卖出信号.

    重构后的实现：
    - 不再硬编码各个策略的分析逻辑
    - 通过StrategyRegistry获取策略实例
    - 调用策略的analyze_current_signal方法
    - 支持任意新增策略，无需修改本服务
    """

    @staticmethod
    def analyze_current_signals(
        df: pd.DataFrame,
        strategy_ids: List[str],
        per_strategy_params: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析当前信号状态.

        Args:
            df: 包含完整OHLCV和指标数据的DataFrame
            strategy_ids: 策略ID列表
            per_strategy_params: 每个策略的参数

        Returns:
            包含分析结果的字典
        """
        if df.empty:
            return {
                "status": "no_data",
                "message": "无可用数据"
            }

        # 获取最新一条数据（最后一天）
        latest = df.iloc[-1]

        analysis_results = []

        for strategy_id in strategy_ids:
            params = per_strategy_params.get(strategy_id, {})

            # 通过注册中心获取策略类
            strategy_class = StrategyRegistry.get(strategy_id)

            if strategy_class is None:
                # 策略未找到
                result = {
                    "strategy_id": strategy_id,
                    "strategy_name": strategy_id,
                    "status": "unknown",
                    "message": f"策略 '{strategy_id}' 未找到"
                }
            else:
                # 创建策略实例并调用其分析方法
                strategy_instance = strategy_class()
                result = strategy_instance.analyze_current_signal(df, params)

            if result:
                analysis_results.append(result)

        return {
            "date": str(latest['date']) if 'date' in latest.index else str(df.index[-1]),
            "close_price": float(latest['close']),
            "analyses": analysis_results
        }
