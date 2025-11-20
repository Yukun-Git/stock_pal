"""数据源故障转移服务.

提供自动故障转移、健康监控和数据源管理功能。
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

from app.adapters import DataAdapterFactory, BaseDataAdapter
from app.adapters.exceptions import (
    DataAdapterException,
    NetworkException,
    TimeoutException,
    DataNotFoundException,
)

logger = logging.getLogger(__name__)


class FailoverService:
    """数据源故障转移服务.

    按优先级尝试多个数据源,自动故障转移。
    """

    # 市场-数据源优先级映射
    DEFAULT_MARKET_PRIORITIES = {
        'A-share': ['akshare', 'baostock', 'yfinance'],
        'HK': ['yfinance', 'akshare'],
        'US': ['yfinance', 'akshare'],
        'Unknown': ['akshare', 'yfinance', 'baostock'],
    }

    def __init__(
        self,
        max_retries: int = 2,
        retry_delay: float = 1.0,
        market_priorities: Optional[Dict[str, List[str]]] = None
    ):
        """初始化服务.

        Args:
            max_retries: 每个适配器最大重试次数
            retry_delay: 重试间隔(秒)
            market_priorities: 市场-数据源优先级映射
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.market_priorities = market_priorities or self.DEFAULT_MARKET_PRIORITIES

        # 健康状态缓存 {adapter_name: health_info}
        self._health_cache: Dict[str, Dict[str, Any]] = {}

        # 性能指标 {adapter_name: {success_count, fail_count, avg_response_ms}}
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def get_stock_data_with_failover(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str = 'qfq',
        preferred_adapter: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """获取股票数据(带故障转移).

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            preferred_adapter: 优先使用的适配器名称

        Returns:
            Tuple[DataFrame, str]: (数据, 使用的适配器名称)

        Raises:
            Exception: 所有数据源均失败
        """
        # 检测市场类型
        market = self._detect_market(symbol)

        # 获取适配器优先级列表
        adapter_names = self._get_adapter_priority(market, preferred_adapter)

        errors = []
        for adapter_name in adapter_names:
            try:
                # 检查适配器是否可用
                if not DataAdapterFactory.is_registered(adapter_name):
                    logger.warning(f"Adapter '{adapter_name}' not registered, skipping")
                    continue

                # 创建适配器实例
                adapter = DataAdapterFactory.create(adapter_name)

                # 检查是否支持该市场
                if not adapter.supports_market(market):
                    logger.debug(f"Adapter '{adapter_name}' doesn't support market '{market}', skipping")
                    continue

                # 尝试获取数据(带重试)
                df = self._fetch_with_retry(
                    adapter, symbol, start_date, end_date, adjust
                )

                if df is not None and not df.empty:
                    logger.info(f"Successfully fetched data using {adapter_name}")
                    return df, adapter_name

            except Exception as e:
                error_msg = f"{adapter_name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Adapter {adapter_name} failed: {e}")
                self._record_failure(adapter_name, str(e))
                continue

        # 所有适配器都失败
        error_summary = "; ".join(errors) if errors else "No available adapters"
        raise Exception(f"All data sources failed for {symbol}: {error_summary}")

    def search_stock_with_failover(
        self,
        keyword: str,
        preferred_adapter: Optional[str] = None
    ) -> Tuple[List[Dict], str]:
        """搜索股票(带故障转移).

        Args:
            keyword: 搜索关键词
            preferred_adapter: 优先使用的适配器

        Returns:
            Tuple[List[Dict], str]: (搜索结果, 使用的适配器名称)
        """
        # 搜索默认使用A股优先级
        adapter_names = self._get_adapter_priority('A-share', preferred_adapter)

        errors = []
        for adapter_name in adapter_names:
            try:
                if not DataAdapterFactory.is_registered(adapter_name):
                    continue

                adapter = DataAdapterFactory.create(adapter_name)

                # 尝试搜索
                results = adapter.search_stock(keyword)

                if results:
                    logger.info(f"Search successful using {adapter_name}, found {len(results)} results")
                    return results, adapter_name

            except Exception as e:
                errors.append(f"{adapter_name}: {str(e)}")
                logger.warning(f"Search failed with {adapter_name}: {e}")
                continue

        # 如果所有适配器都失败或无结果
        if errors:
            raise Exception(f"All search sources failed: {'; '.join(errors)}")

        return [], adapter_names[0] if adapter_names else 'unknown'

    def _fetch_with_retry(
        self,
        adapter: BaseDataAdapter,
        symbol: str,
        start_date: str,
        end_date: str,
        adjust: str
    ) -> Optional[pd.DataFrame]:
        """带重试的数据获取.

        Args:
            adapter: 适配器实例
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型

        Returns:
            DataFrame或None
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                df = adapter.get_stock_data(symbol, start_date, end_date, adjust)
                response_time = (time.time() - start_time) * 1000

                # 记录成功指标
                self._record_success(adapter.name, response_time)

                return df

            except (NetworkException, TimeoutException) as e:
                # 网络错误,可以重试
                last_error = e
                if attempt < self.max_retries:
                    logger.debug(f"Retry {attempt + 1}/{self.max_retries} for {adapter.name}")
                    time.sleep(self.retry_delay)
                continue

            except DataNotFoundException:
                # 数据不存在,不重试
                raise

            except Exception as e:
                # 其他错误,重试一次
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                continue

        if last_error:
            raise last_error
        return None

    def _get_adapter_priority(
        self,
        market: str,
        preferred_adapter: Optional[str] = None
    ) -> List[str]:
        """获取适配器优先级列表.

        Args:
            market: 市场类型
            preferred_adapter: 优先使用的适配器

        Returns:
            适配器名称列表(按优先级排序)
        """
        # 获取默认优先级
        priorities = self.market_priorities.get(
            market,
            self.market_priorities.get('Unknown', ['akshare'])
        ).copy()

        # 如果指定了优先适配器,将其移到最前
        if preferred_adapter and preferred_adapter in priorities:
            priorities.remove(preferred_adapter)
            priorities.insert(0, preferred_adapter)
        elif preferred_adapter:
            priorities.insert(0, preferred_adapter)

        return priorities

    def _detect_market(self, symbol: str) -> str:
        """检测股票市场类型.

        Args:
            symbol: 股票代码

        Returns:
            市场类型
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

    def _record_success(self, adapter_name: str, response_time_ms: float):
        """记录成功指标.

        Args:
            adapter_name: 适配器名称
            response_time_ms: 响应时间(毫秒)
        """
        if adapter_name not in self._metrics:
            self._metrics[adapter_name] = {
                'success_count': 0,
                'fail_count': 0,
                'total_response_ms': 0,
                'last_success': None,
                'last_failure': None,
            }

        metrics = self._metrics[adapter_name]
        metrics['success_count'] += 1
        metrics['total_response_ms'] += response_time_ms
        metrics['last_success'] = datetime.now().isoformat()

    def _record_failure(self, adapter_name: str, error: str):
        """记录失败指标.

        Args:
            adapter_name: 适配器名称
            error: 错误信息
        """
        if adapter_name not in self._metrics:
            self._metrics[adapter_name] = {
                'success_count': 0,
                'fail_count': 0,
                'total_response_ms': 0,
                'last_success': None,
                'last_failure': None,
            }

        metrics = self._metrics[adapter_name]
        metrics['fail_count'] += 1
        metrics['last_failure'] = datetime.now().isoformat()
        metrics['last_error'] = error

    def get_metrics(self, adapter_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能指标.

        Args:
            adapter_name: 适配器名称,None表示获取所有

        Returns:
            指标字典
        """
        if adapter_name:
            metrics = self._metrics.get(adapter_name, {})
            if metrics and metrics.get('success_count', 0) > 0:
                metrics['avg_response_ms'] = round(
                    metrics['total_response_ms'] / metrics['success_count'], 2
                )
            return metrics

        # 返回所有指标
        result = {}
        for name, metrics in self._metrics.items():
            result[name] = metrics.copy()
            if metrics.get('success_count', 0) > 0:
                result[name]['avg_response_ms'] = round(
                    metrics['total_response_ms'] / metrics['success_count'], 2
                )
        return result

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """对所有已注册适配器进行健康检查.

        Returns:
            {adapter_name: health_info}
        """
        results = {}
        adapter_names = DataAdapterFactory.get_available_adapters()

        for name in adapter_names:
            try:
                adapter = DataAdapterFactory.create(name)
                health = adapter.health_check()
                results[name] = health
                self._health_cache[name] = health
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'message': str(e),
                    'checked_at': datetime.now().isoformat()
                }

        return results

    def get_adapter_status(self) -> List[Dict[str, Any]]:
        """获取所有适配器状态.

        Returns:
            适配器状态列表
        """
        adapter_names = DataAdapterFactory.get_available_adapters()
        statuses = []

        for name in adapter_names:
            try:
                adapter = DataAdapterFactory.create(name)
                metadata = adapter.get_metadata()

                # 添加健康状态
                health = self._health_cache.get(name, {})
                metadata['health_status'] = health.get('status', 'unknown')
                metadata['last_check'] = health.get('checked_at')

                # 添加性能指标
                metrics = self.get_metrics(name)
                metadata['metrics'] = metrics

                statuses.append(metadata)
            except Exception as e:
                statuses.append({
                    'name': name,
                    'error': str(e)
                })

        return statuses


# 全局单例
_failover_service: Optional[FailoverService] = None


def get_failover_service() -> FailoverService:
    """获取故障转移服务单例.

    Returns:
        FailoverService实例
    """
    global _failover_service
    if _failover_service is None:
        _failover_service = FailoverService()
    return _failover_service
