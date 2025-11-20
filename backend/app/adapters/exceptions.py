"""数据适配器异常类定义.

定义数据源适配器使用的统一异常类型体系。
"""


class DataAdapterException(Exception):
    """数据适配器异常基类.

    所有数据适配器相关的异常都应继承此类。
    """

    def __init__(self, message: str, adapter_name: str = None, original_error: Exception = None):
        """初始化异常.

        Args:
            message: 错误消息
            adapter_name: 适配器名称（可选）
            original_error: 原始异常（可选）
        """
        self.message = message
        self.adapter_name = adapter_name
        self.original_error = original_error

        # 构建完整错误消息
        full_message = message
        if adapter_name:
            full_message = f"[{adapter_name}] {message}"
        if original_error:
            full_message += f" | Original error: {str(original_error)}"

        super().__init__(full_message)


class NetworkException(DataAdapterException):
    """网络异常.

    网络请求失败、连接超时等网络相关错误。
    此异常通常可以重试。
    """

    def __init__(self, message: str = "Network error occurred", **kwargs):
        super().__init__(message, **kwargs)


class TimeoutException(DataAdapterException):
    """超时异常.

    请求超时错误。
    此异常通常可以重试。
    """

    def __init__(self, message: str = "Request timeout", **kwargs):
        super().__init__(message, **kwargs)


class AuthenticationException(DataAdapterException):
    """认证异常.

    API密钥无效、Token过期等认证失败错误。
    此异常不应重试，需要用户更新配置。
    """

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class RateLimitException(DataAdapterException):
    """限流异常.

    超出API调用频率限制或配额限制。
    此异常不应在同一数据源重试，应切换到其他数据源。
    """

    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(message, **kwargs)


class DataNotFoundException(DataAdapterException):
    """数据未找到异常.

    请求的股票代码不存在、日期范围无数据等。
    此异常不应重试。
    """

    def __init__(self, message: str = "Data not found", **kwargs):
        super().__init__(message, **kwargs)


class DataFormatException(DataAdapterException):
    """数据格式异常.

    返回的数据格式错误、字段缺失、数据解析失败等。
    此异常可能表示数据源API变更，应记录并告警。
    """

    def __init__(self, message: str = "Data format error", **kwargs):
        super().__init__(message, **kwargs)


class UnsupportedMarketException(DataAdapterException):
    """不支持的市场异常.

    适配器不支持请求的市场类型（如某适配器不支持港股）。
    此异常不应重试，应切换到支持该市场的数据源。
    """

    def __init__(self, message: str = "Market not supported", market: str = None, **kwargs):
        self.market = market
        if market:
            message = f"{message}: {market}"
        super().__init__(message, **kwargs)


# 异常处理策略映射
RETRYABLE_EXCEPTIONS = (
    NetworkException,
    TimeoutException,
)

NON_RETRYABLE_EXCEPTIONS = (
    AuthenticationException,
    DataNotFoundException,
    UnsupportedMarketException,
)

SWITCHABLE_EXCEPTIONS = (
    RateLimitException,
    DataFormatException,
)


def is_retryable(exception: Exception) -> bool:
    """判断异常是否可重试.

    Args:
        exception: 异常对象

    Returns:
        True表示可以重试，False表示不应重试
    """
    return isinstance(exception, RETRYABLE_EXCEPTIONS)


def should_switch_adapter(exception: Exception) -> bool:
    """判断是否应切换到其他适配器.

    Args:
        exception: 异常对象

    Returns:
        True表示应切换适配器，False表示可以继续使用当前适配器
    """
    return isinstance(exception, SWITCHABLE_EXCEPTIONS)


def get_exception_category(exception: Exception) -> str:
    """获取异常类别.

    Args:
        exception: 异常对象

    Returns:
        异常类别: 'retryable', 'non-retryable', 'switchable', 'unknown'
    """
    if isinstance(exception, RETRYABLE_EXCEPTIONS):
        return 'retryable'
    elif isinstance(exception, NON_RETRYABLE_EXCEPTIONS):
        return 'non-retryable'
    elif isinstance(exception, SWITCHABLE_EXCEPTIONS):
        return 'switchable'
    else:
        return 'unknown'
