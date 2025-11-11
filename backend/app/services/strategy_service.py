"""策略服务 - 作为策略注册器的门面."""

import pandas as pd
from typing import Dict, Any, List
# Import strategies module to trigger strategy registration
import app.strategies  # noqa: F401
from app.strategies.registry import StrategyRegistry
from app.services.data_service import DataService


class StrategyService:
    """策略服务.

    作为StrategyRegistry的门面，提供策略相关的服务接口。
    保持API向后兼容，内部使用新的策略注册系统。
    """

    @staticmethod
    def get_all_strategies() -> List[Dict[str, Any]]:
        """获取所有已注册策略.

        Returns:
            策略元数据列表，包含id, name, description, category, parameters
        """
        return StrategyRegistry.get_all()

    @staticmethod
    def apply_strategy(
        strategy_id: str,
        df: pd.DataFrame,
        params: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """应用策略生成交易信号.

        Args:
            strategy_id: 策略ID
            df: 包含价格和指标数据的DataFrame
            params: 策略参数

        Returns:
            添加了'signal'列的DataFrame (1=买入, -1=卖出, 0=持有)

        Raises:
            ValueError: 如果策略不存在
        """
        if params is None:
            params = {}

        # 如果指定了timeframe且不是日线，先进行周期转换
        timeframe = params.get('timeframe', 'D')
        if timeframe != 'D':
            df = DataService.resample_to_timeframe(df, timeframe)

        # 应用策略
        return StrategyRegistry.apply_strategy(strategy_id, df, params)


# 注意：旧的策略定义已迁移到 app/strategies/ 目录
# 策略会在模块导入时自动注册到 StrategyRegistry
