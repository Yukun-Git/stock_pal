"""数据适配器工厂.

提供数据适配器的创建和管理功能。
"""

from typing import Dict, Type
from .base import BaseDataAdapter


class DataAdapterFactory:
    """数据适配器工厂类.

    使用注册模式管理所有可用的数据适配器。
    支持根据配置名称动态创建适配器实例。
    """

    # 适配器注册表: {适配器名称: 适配器类}
    _adapters: Dict[str, Type[BaseDataAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: Type[BaseDataAdapter]) -> None:
        """注册数据适配器.

        Args:
            name: 适配器标识名称 (e.g., 'akshare', 'yfinance')
            adapter_class: 适配器类

        Raises:
            ValueError: 如果适配器名称已存在
        """
        if name in cls._adapters:
            raise ValueError(f"Adapter '{name}' is already registered")

        if not issubclass(adapter_class, BaseDataAdapter):
            raise ValueError(f"Adapter class must inherit from BaseDataAdapter")

        cls._adapters[name] = adapter_class
        print(f"Registered data adapter: {name} -> {adapter_class.__name__}")

    @classmethod
    def create(cls, name: str) -> BaseDataAdapter:
        """创建数据适配器实例.

        Args:
            name: 适配器名称

        Returns:
            适配器实例

        Raises:
            ValueError: 如果适配器未注册
        """
        if name not in cls._adapters:
            available = ', '.join(cls._adapters.keys())
            raise ValueError(
                f"Unknown adapter: '{name}'. "
                f"Available adapters: {available}"
            )

        adapter_class = cls._adapters[name]
        return adapter_class()

    @classmethod
    def get_available_adapters(cls) -> list:
        """获取所有已注册的适配器名称.

        Returns:
            适配器名称列表
        """
        return list(cls._adapters.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """检查适配器是否已注册.

        Args:
            name: 适配器名称

        Returns:
            是否已注册
        """
        return name in cls._adapters


# 自动注册内置适配器
def _register_builtin_adapters():
    """注册所有内置的数据适配器."""
    from .akshare_adapter import AkShareAdapter
    from .yfinance_adapter import YFinanceAdapter

    DataAdapterFactory.register('akshare', AkShareAdapter)
    DataAdapterFactory.register('yfinance', YFinanceAdapter)


# 模块加载时自动注册
_register_builtin_adapters()
