"""策略基类定义."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd


class BaseStrategy(ABC):
    """交易策略基类.

    所有策略必须继承此类并实现 generate_signals 方法。
    子类需要定义策略元数据（strategy_id, name, description, category）。
    """

    # 策略元数据（子类必须定义）
    strategy_id: str = None           # 策略ID（唯一标识）
    name: str = None                  # 策略名称
    description: str = None           # 策略描述
    category: str = None              # 策略分类：pattern/indicator/custom

    @classmethod
    def get_parameters(cls) -> List[Dict[str, Any]]:
        """返回策略参数定义.

        子类可以重写此方法来定义自己的参数，
        也可以调用 super().get_parameters() 来继承基类参数。

        Returns:
            参数定义列表，每个参数包含：name, label, type, default, options等
        """
        return [
            {
                'name': 'timeframe',
                'label': '时间周期',
                'type': 'select',
                'default': 'D',
                'options': [
                    {'value': 'D', 'label': '日线'},
                    {'value': 'W', 'label': '周线'},
                ],
                'description': '策略运行的时间周期'
            },
            {
                'name': 'hold_periods',
                'label': '持有周期数',
                'type': 'integer',
                'default': 5,
                'min': 1,
                'max': 30,
                'description': '买入后持有的周期数（日线为天数，周线为周数）'
            }
        ]

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """生成交易信号（子类必须实现）.

        Args:
            df: 包含价格和指标数据的DataFrame，必须包含OHLCV列
            params: 策略参数字典，包含用户设置的参数值

        Returns:
            添加了 'signal' 列的DataFrame
            signal取值: 1=买入信号, -1=卖出信号, 0=持有/无信号
        """
        pass

    def analyze_current_signal(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前信号接近度（可选实现）.

        子类可以重写此方法来提供实时信号分析。
        默认实现返回通用的"不支持"消息。

        Args:
            df: 包含价格和指标数据的DataFrame，必须包含OHLCV列
            params: 策略参数字典，包含用户设置的参数值

        Returns:
            包含分析结果的字典，格式为：
            {
                "strategy_id": str,        # 策略ID
                "strategy_name": str,      # 策略名称
                "status": str,             # 当前状态：bullish/bearish/neutral等
                "proximity": str,          # 接近程度：very_close/close/moderate/far
                "indicators": dict,        # 当前指标值
                "current_state": str,      # 当前状态描述
                "proximity_description": str,  # 接近度描述
                "suggestion": str          # 操作建议
            }
        """
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.name,
            "status": "unknown",
            "message": "此策略暂不支持信号分析"
        }

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为API返回格式.

        Returns:
            包含策略完整信息的字典，用于API响应
        """
        return {
            'id': cls.strategy_id,
            'name': cls.name,
            'description': cls.description,
            'category': cls.category,
            'parameters': cls.get_parameters()
        }

    @classmethod
    def validate_metadata(cls):
        """验证策略元数据是否完整.

        Raises:
            ValueError: 如果元数据缺失
        """
        if not cls.strategy_id:
            raise ValueError(f"Strategy {cls.__name__} must define strategy_id")
        if not cls.name:
            raise ValueError(f"Strategy {cls.__name__} must define name")
        if not cls.description:
            raise ValueError(f"Strategy {cls.__name__} must define description")
        if not cls.category:
            raise ValueError(f"Strategy {cls.__name__} must define category")
