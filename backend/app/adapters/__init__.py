"""数据源适配器模块.

提供统一的数据获取接口，支持多种数据源。
"""

from .base import BaseDataAdapter
from .factory import DataAdapterFactory
from .akshare_adapter import AkShareAdapter
from .yfinance_adapter import YFinanceAdapter

__all__ = [
    'BaseDataAdapter',
    'DataAdapterFactory',
    'AkShareAdapter',
    'YFinanceAdapter',
]
