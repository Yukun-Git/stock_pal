"""策略模块.

此模块包含所有交易策略的实现。
策略按类型组织在子目录中：
  - pattern: K线形态策略
  - indicator: 技术指标策略
"""

from .base import BaseStrategy
from .registry import StrategyRegistry

# 导入所有策略以触发注册
# 这样可以确保所有策略都被自动注册到StrategyRegistry中
from .pattern import *
from .indicator import *

__all__ = [
    'BaseStrategy',
    'StrategyRegistry',
]
