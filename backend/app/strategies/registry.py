"""策略注册中心."""

from typing import Dict, Type, List, Any
import pandas as pd
from .base import BaseStrategy


class StrategyRegistry:
    """策略注册中心.

    负责策略的注册、获取和调用。
    使用装饰器模式实现自动注册。
    """

    _strategies: Dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def register(cls, strategy_class: Type[BaseStrategy]):
        """注册策略类（装饰器）.

        使用方法:
            @StrategyRegistry.register
            class MyStrategy(BaseStrategy):
                ...

        Args:
            strategy_class: 策略类

        Returns:
            原策略类（不改变类本身）

        Raises:
            ValueError: 如果策略元数据不完整
        """
        # 验证元数据
        strategy_class.validate_metadata()

        # 检查重复注册
        if strategy_class.strategy_id in cls._strategies:
            raise ValueError(
                f"Strategy ID '{strategy_class.strategy_id}' already registered"
            )

        # 注册策略
        cls._strategies[strategy_class.strategy_id] = strategy_class
        return strategy_class

    @classmethod
    def get(cls, strategy_id: str) -> Type[BaseStrategy]:
        """获取策略类.

        Args:
            strategy_id: 策略ID

        Returns:
            策略类

        Raises:
            ValueError: 如果策略不存在
        """
        if strategy_id not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy_id}")
        return cls._strategies[strategy_id]

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """获取所有已注册策略的元数据.

        Returns:
            策略元数据列表，每个元素包含id, name, description, category, parameters
        """
        return [
            strategy.to_dict()
            for strategy in cls._strategies.values()
        ]

    @classmethod
    def apply_strategy(
        cls,
        strategy_id: str,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """应用策略生成交易信号.

        Args:
            strategy_id: 策略ID
            df: 包含价格和指标数据的DataFrame
            params: 策略参数字典

        Returns:
            添加了信号列的DataFrame

        Raises:
            ValueError: 如果策略不存在
        """
        strategy_class = cls.get(strategy_id)
        strategy_instance = strategy_class()
        return strategy_instance.generate_signals(df, params)

    @classmethod
    def list_strategy_ids(cls) -> List[str]:
        """获取所有策略ID列表.

        Returns:
            策略ID列表
        """
        return list(cls._strategies.keys())

    @classmethod
    def get_strategy_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """按分类获取策略.

        Args:
            category: 策略分类（pattern/indicator/custom）

        Returns:
            该分类下的策略元数据列表
        """
        return [
            strategy.to_dict()
            for strategy in cls._strategies.values()
            if strategy.category == category
        ]
