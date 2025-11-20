"""数据源适配器模块.

提供统一的数据获取接口，支持多种数据源。
"""

from .base import BaseDataAdapter
from .factory import DataAdapterFactory
from .akshare_adapter import AkShareAdapter
from .yfinance_adapter import YFinanceAdapter
from .baostock_adapter import BaostockAdapter
from .registry import (
    register_adapter,
    get_adapter_class,
    get_all_adapters,
    get_adapter_names,
    is_adapter_registered,
    create_adapter,
)
from .exceptions import (
    DataAdapterException,
    NetworkException,
    TimeoutException,
    AuthenticationException,
    DataNotFoundException,
    DataFormatException,
    UnsupportedMarketException,
)

__all__ = [
    # Base classes
    'BaseDataAdapter',
    'DataAdapterFactory',
    # Adapters
    'AkShareAdapter',
    'YFinanceAdapter',
    'BaostockAdapter',
    # Registry
    'register_adapter',
    'get_adapter_class',
    'get_all_adapters',
    'get_adapter_names',
    'is_adapter_registered',
    'create_adapter',
    # Exceptions
    'DataAdapterException',
    'NetworkException',
    'TimeoutException',
    'AuthenticationException',
    'DataNotFoundException',
    'DataFormatException',
    'UnsupportedMarketException',
]
