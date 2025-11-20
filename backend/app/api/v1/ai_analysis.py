"""AI智能分析API.

提供回测结果的AI智能分析接口。
"""

from flask import request
from flask_restful import Resource
import logging

from app.services.ai_analysis_service import get_ai_analysis_service

logger = logging.getLogger(__name__)


class BacktestAnalyzeResource(Resource):
    """回测AI分析资源.

    POST /api/v1/backtest/analyze - 分析回测结果
    """

    def post(self):
        """分析回测结果.

        Request Body:
        {
            "stock_info": {
                "symbol": "600000",
                "name": "浦发银行",
                "period": "2023-01-01 至 2024-12-31"
            },
            "strategy_info": {
                "name": "MACD金叉策略",
                "description": "..."
            },
            "parameters": {
                "initial_capital": 100000,
                "commission_rate": 0.0003,
                "strategy_params": {...}
            },
            "backtest_results": {
                "total_return": 0.25,
                "win_rate": 0.55,
                ...
            }
        }

        Response:
        {
            "success": true,
            "data": {
                "analysis": "AI分析结果（Markdown）",
                "tokens_used": 1234,
                "model": "qwen-plus",
                "analysis_time": 3.5
            }
        }
        """
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return {
                    'success': False,
                    'message': '请求数据为空'
                }, 400

            # 验证必需字段
            required_fields = ['stock_info', 'strategy_info', 'parameters', 'backtest_results']
            for field in required_fields:
                if field not in data:
                    return {
                        'success': False,
                        'message': f'缺少必需字段: {field}'
                    }, 400

            # 获取AI分析服务
            ai_service = get_ai_analysis_service()

            # 检查服务是否配置
            if not ai_service.is_configured():
                return {
                    'success': False,
                    'message': 'AI分析服务未配置。请联系管理员配置QWEN_API_KEY。'
                }, 503

            # 执行分析
            result = ai_service.analyze_backtest(data)

            if result['success']:
                return {
                    'success': True,
                    'data': {
                        'analysis': result['analysis'],
                        'tokens_used': result['tokens_used'],
                        'model': result['model'],
                        'analysis_time': result['analysis_time']
                    }
                }, 200
            else:
                return {
                    'success': False,
                    'message': result.get('error', 'AI分析失败')
                }, 500

        except Exception as e:
            logger.error(f"Backtest analyze failed: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }, 500
