"""数据源适配器管理API.

提供数据源状态查询、健康检查和配置管理接口。
"""

from flask_restful import Resource
import logging

from app.services.failover_service import get_failover_service
from app.adapters import DataAdapterFactory

logger = logging.getLogger(__name__)


class AdapterStatusResource(Resource):
    """适配器状态资源.

    GET /api/v1/adapters/status - 获取所有适配器状态
    """

    def get(self):
        """获取所有适配器状态."""
        try:
            service = get_failover_service()
            statuses = service.get_adapter_status()

            return {
                'status': 'success',
                'data': statuses
            }, 200

        except Exception as e:
            logger.error(f"Failed to get adapter status: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }, 500


class AdapterHealthResource(Resource):
    """适配器健康检查资源.

    GET /api/v1/adapters/health - 执行所有适配器的健康检查
    """

    def get(self):
        """执行健康检查."""
        try:
            service = get_failover_service()
            health_results = service.health_check_all()

            # 统计健康状态
            total = len(health_results)
            online = sum(1 for h in health_results.values() if h.get('status') == 'online')
            offline = sum(1 for h in health_results.values() if h.get('status') == 'offline')
            error = total - online - offline

            return {
                'status': 'success',
                'data': {
                    'summary': {
                        'total': total,
                        'online': online,
                        'offline': offline,
                        'error': error
                    },
                    'adapters': health_results
                }
            }, 200

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }, 500


class AdapterMetricsResource(Resource):
    """适配器性能指标资源.

    GET /api/v1/adapters/metrics - 获取所有适配器的性能指标
    GET /api/v1/adapters/metrics/<name> - 获取指定适配器的性能指标
    """

    def get(self, name=None):
        """获取性能指标.

        Args:
            name: 适配器名称(可选)
        """
        try:
            service = get_failover_service()

            if name:
                # 检查适配器是否存在
                if not DataAdapterFactory.is_registered(name):
                    return {
                        'status': 'error',
                        'message': f"Adapter '{name}' not found"
                    }, 404

                metrics = service.get_metrics(name)
                return {
                    'status': 'success',
                    'data': metrics
                }, 200
            else:
                # 返回所有指标
                metrics = service.get_metrics()
                return {
                    'status': 'success',
                    'data': metrics
                }, 200

        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }, 500


class AdapterListResource(Resource):
    """适配器列表资源.

    GET /api/v1/adapters - 获取所有已注册的适配器
    """

    def get(self):
        """获取适配器列表."""
        try:
            adapter_names = DataAdapterFactory.get_available_adapters()

            adapters = []
            for name in adapter_names:
                try:
                    adapter = DataAdapterFactory.create(name)
                    metadata = adapter.get_metadata()
                    adapters.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to get metadata for {name}: {e}")
                    adapters.append({
                        'name': name,
                        'error': str(e)
                    })

            return {
                'status': 'success',
                'data': adapters
            }, 200

        except Exception as e:
            logger.error(f"Failed to list adapters: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }, 500
