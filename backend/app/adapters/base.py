"""数据适配器基类.

定义所有数据源适配器必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd


class BaseDataAdapter(ABC):
    """数据源适配器抽象基类.

    所有数据源适配器都必须继承此类并实现所有抽象方法。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """适配器名称 (唯一标识符)."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """适配器显示名称 (用于UI展示)."""
        pass

    @property
    @abstractmethod
    def supported_markets(self) -> List[str]:
        """支持的市场类型列表.

        Returns:
            市场类型列表，如 ['A-share', 'HK', 'US']
        """
        pass

    @property
    def requires_auth(self) -> bool:
        """是否需要API密钥或Token认证.

        Returns:
            True表示需要认证，False表示无需认证
        """
        return False

    @property
    def timeout(self) -> int:
        """请求超时时间（秒）.

        Returns:
            超时时间，默认10秒
        """
        return 10

    @abstractmethod
    def get_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """获取股票历史数据.

        Args:
            symbol: 股票代码 (e.g., '000001', '600519.SH', '00700.HK')
            start_date: 开始日期 'YYYYMMDD' 格式
            end_date: 结束日期 'YYYYMMDD' 格式
            adjust: 复权类型 ('qfq'=前复权, 'hfq'=后复权, ''=不复权)

        Returns:
            DataFrame包含以下标准列:
            - date: 日期 (datetime)
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额 (可选)
            - amplitude: 振幅 (可选)
            - pct_change: 涨跌幅 (可选)
            - change: 涨跌额 (可选)
            - turnover: 换手率 (可选)

        Raises:
            Exception: 获取数据失败时抛出异常
        """
        pass

    @abstractmethod
    def search_stock(self, keyword: str) -> list:
        """搜索股票.

        Args:
            keyword: 搜索关键词 (股票代码或名称)

        Returns:
            股票列表，每个元素是包含 code 和 name 的字典

        Raises:
            Exception: 搜索失败时抛出异常
        """
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> dict:
        """获取股票基本信息.

        Args:
            symbol: 股票代码

        Returns:
            包含股票基本信息的字典:
            - code: 股票代码
            - name: 股票名称
            - market: 市场类型 (e.g., 'A-share', 'HK', 'US')

        Raises:
            Exception: 获取失败时返回通用信息
        """
        pass

    def _detect_market(self, symbol: str) -> str:
        """检测股票市场类型.

        Args:
            symbol: 股票代码

        Returns:
            市场类型: 'A-share', 'HK', 'US', 'Unknown'
        """
        # 港股检测
        if '.HK' in symbol.upper():
            return 'HK'

        # 美股检测 (通常有点号但不是.HK/.SH/.SZ)
        if '.' in symbol and not any(x in symbol.upper() for x in ['.SH', '.SZ']):
            return 'US'

        # A股检测
        base_symbol = symbol.split('.')[0]
        if base_symbol.isdigit() and len(base_symbol) == 6:
            if base_symbol.startswith('6'):
                return 'A-share'  # 上海
            elif base_symbol.startswith(('0', '3')):
                return 'A-share'  # 深圳
            elif base_symbol.startswith('8') or base_symbol.startswith('4'):
                return 'A-share'  # 北交所

        return 'Unknown'

    def _normalize_stock_code(self, symbol: str) -> str:
        """规范化股票代码.

        移除可选的交易所后缀，返回基础代码。

        Args:
            symbol: 股票代码

        Returns:
            规范化后的代码
        """
        # 港股：移除 .HK
        if '.HK' in symbol.upper():
            return symbol.replace('.HK', '').replace('.hk', '')

        # A股：移除 .SH/.SZ
        if '.' in symbol:
            return symbol.split('.')[0]

        return symbol

    def supports_market(self, market: str) -> bool:
        """检查适配器是否支持指定市场.

        Args:
            market: 市场类型

        Returns:
            是否支持
        """
        return market in self.supported_markets

    def health_check(self) -> Dict[str, Any]:
        """健康检查.

        测试适配器是否正常工作。

        Returns:
            健康检查结果字典:
            {
                'status': 'online' | 'offline' | 'error',
                'response_time_ms': float,
                'message': str,
                'checked_at': str (ISO格式时间戳)
            }
        """
        import time
        from datetime import datetime

        try:
            start_time = time.time()

            # 尝试获取测试股票数据（A股：平安银行）
            test_symbol = '000001'
            test_start = '20231201'
            test_end = '20231201'

            df = self.get_stock_data(test_symbol, test_start, test_end)

            response_time = (time.time() - start_time) * 1000

            if df is not None and len(df) > 0:
                return {
                    'status': 'online',
                    'response_time_ms': round(response_time, 2),
                    'message': 'Health check passed',
                    'checked_at': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'response_time_ms': round(response_time, 2),
                    'message': 'No data returned',
                    'checked_at': datetime.now().isoformat()
                }

        except Exception as e:
            return {
                'status': 'offline',
                'response_time_ms': 0,
                'message': f'Health check failed: {str(e)}',
                'checked_at': datetime.now().isoformat()
            }

    def validate_config(self) -> bool:
        """验证配置是否正确.

        检查适配器所需的配置（如API密钥）是否有效。

        Returns:
            True表示配置有效，False表示配置无效
        """
        # 默认实现：不需要认证的适配器总是有效
        if not self.requires_auth:
            return True

        # 需要认证的适配器应该覆盖此方法
        return False

    def get_metadata(self) -> Dict[str, Any]:
        """获取适配器元数据.

        Returns:
            元数据字典:
            {
                'name': str,
                'display_name': str,
                'supported_markets': List[str],
                'requires_auth': bool,
                'timeout': int,
                'version': str (可选)
            }
        """
        return {
            'name': self.name,
            'display_name': self.display_name,
            'supported_markets': self.supported_markets,
            'requires_auth': self.requires_auth,
            'timeout': self.timeout
        }
