"""适配器注册机制.

提供装饰器方式注册数据适配器。
"""

from typing import Type, Optional
from functools import wraps

from .base import BaseDataAdapter


# 全局适配器注册表
_adapter_registry = {}


def register_adapter(name: Optional[str] = None):
    """适配器注册装饰器.

    用于将数据适配器类注册到全局注册表中。

    Args:
        name: 可选的适配器名称。如果不提供，则使用类的name属性。

    Returns:
        装饰器函数

    Example:
        @register_adapter('akshare')
        class AkShareAdapter(BaseDataAdapter):
            ...

        # 或者不指定名称，使用类的name属性
        @register_adapter()
        class BaostockAdapter(BaseDataAdapter):
            @property
            def name(self):
                return 'baostock'
    """
    def decorator(cls: Type[BaseDataAdapter]):
        if not issubclass(cls, BaseDataAdapter):
            raise ValueError(
                f"Adapter class {cls.__name__} must inherit from BaseDataAdapter"
            )

        # 确定适配器名称
        adapter_name = name
        if adapter_name is None:
            # 创建临时实例获取name属性
            try:
                temp_instance = cls()
                adapter_name = temp_instance.name
            except Exception:
                # 如果无法实例化，使用类名小写
                adapter_name = cls.__name__.lower().replace('adapter', '')

        # 检查重复注册
        if adapter_name in _adapter_registry:
            raise ValueError(
                f"Adapter '{adapter_name}' is already registered by "
                f"{_adapter_registry[adapter_name].__name__}"
            )

        # 注册适配器
        _adapter_registry[adapter_name] = cls
        print(f"[Registry] Registered adapter: {adapter_name} -> {cls.__name__}")

        return cls

    return decorator


def get_adapter_class(name: str) -> Type[BaseDataAdapter]:
    """获取已注册的适配器类.

    Args:
        name: 适配器名称

    Returns:
        适配器类

    Raises:
        ValueError: 如果适配器未注册
    """
    if name not in _adapter_registry:
        available = ', '.join(_adapter_registry.keys()) or 'none'
        raise ValueError(
            f"Unknown adapter: '{name}'. Available adapters: {available}"
        )
    return _adapter_registry[name]


def get_all_adapters():
    """获取所有已注册的适配器.

    Returns:
        dict: {适配器名称: 适配器类}
    """
    return dict(_adapter_registry)


def get_adapter_names():
    """获取所有已注册的适配器名称.

    Returns:
        list: 适配器名称列表
    """
    return list(_adapter_registry.keys())


def is_adapter_registered(name: str) -> bool:
    """检查适配器是否已注册.

    Args:
        name: 适配器名称

    Returns:
        是否已注册
    """
    return name in _adapter_registry


def create_adapter(name: str) -> BaseDataAdapter:
    """创建适配器实例.

    Args:
        name: 适配器名称

    Returns:
        适配器实例
    """
    adapter_class = get_adapter_class(name)
    return adapter_class()
