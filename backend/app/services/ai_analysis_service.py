"""AI智能分析服务.

使用阿里云通义千问-Plus API分析回测结果。
"""

import os
import logging
from typing import Dict, Any, Optional
import requests
from flask import current_app

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """AI分析服务.

    使用阿里云通义千问API分析回测结果，提供策略优化建议。
    """

    # 阿里云DashScope API配置
    DEFAULT_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    DEFAULT_MODEL = "qwen-plus"
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_TOKENS = 1000

    # 系统提示词模板
    SYSTEM_PROMPT = """你是一位专业的量化交易策略分析师，专门为散户投资者分析回测结果。

用户刚刚完成了一次股票回测，你需要：
1. 从专业角度评估策略表现
2. 用通俗易懂的语言解释关键指标
3. 给出具体可执行的优化建议
4. 提示潜在风险

请用结构化的Markdown格式回复，包含以下部分：
## 策略表现评估
## 风险分析
## 参数优化建议
## 改进方向

注意：
- 避免使用过于专业的术语
- 给出的建议要具体可执行
- 保持客观，既要指出优势也要指出不足
- 控制回复长度在500-800字"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_tokens: Optional[int] = None
    ):
        """初始化AI分析服务.

        Args:
            api_key: 阿里云API密钥，None时从环境变量读取
            api_url: API地址，None时使用默认
            model: 模型名称，None时使用qwen-plus
            timeout: 超时时间（秒），None时使用30秒
            max_tokens: 最大token数，None时使用1000
        """
        self.api_key = api_key or os.getenv('QWEN_API_KEY') or current_app.config.get('QWEN_API_KEY')
        self.api_url = api_url or os.getenv('QWEN_API_URL', self.DEFAULT_API_URL)
        self.model = model or os.getenv('QWEN_MODEL', self.DEFAULT_MODEL)
        self.timeout = timeout or int(os.getenv('QWEN_TIMEOUT', str(self.DEFAULT_TIMEOUT)))
        self.max_tokens = max_tokens or int(os.getenv('QWEN_MAX_TOKENS', str(self.DEFAULT_MAX_TOKENS)))

        if not self.api_key:
            logger.warning("QWEN_API_KEY not configured. AI analysis will be disabled.")

    def analyze_backtest(self, backtest_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析回测结果.

        Args:
            backtest_data: 回测数据，包含股票信息、策略信息、参数和结果

        Returns:
            分析结果字典:
            {
                'success': bool,
                'analysis': str,  # Markdown格式的分析文本
                'tokens_used': int,
                'model': str,
                'analysis_time': float,
                'error': str  # 失败时包含
            }
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'AI分析服务未配置API密钥'
            }

        try:
            # 构建用户提示词
            user_prompt = self._build_user_prompt(backtest_data)

            # 调用API
            import time
            start_time = time.time()

            response_data = self._call_qwen_api(user_prompt)

            analysis_time = time.time() - start_time

            # 解析响应
            if response_data.get('output', {}).get('text'):
                analysis_text = response_data['output']['text']
                tokens_used = response_data.get('usage', {}).get('total_tokens', 0)

                return {
                    'success': True,
                    'analysis': analysis_text,
                    'tokens_used': tokens_used,
                    'model': self.model,
                    'analysis_time': round(analysis_time, 2)
                }
            else:
                logger.error(f"Unexpected API response: {response_data}")
                return {
                    'success': False,
                    'error': 'AI返回数据格式异常'
                }

        except requests.exceptions.Timeout:
            logger.error("Qwen API timeout")
            return {
                'success': False,
                'error': 'AI分析超时，请稍后重试'
            }
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                'success': False,
                'error': f'AI分析失败: {str(e)}'
            }

    def _build_user_prompt(self, backtest_data: Dict[str, Any]) -> str:
        """构建用户提示词.

        Args:
            backtest_data: 回测数据

        Returns:
            格式化的提示词
        """
        stock_info = backtest_data.get('stock_info', {})
        strategy_info = backtest_data.get('strategy_info', {})
        parameters = backtest_data.get('parameters', {})
        results = backtest_data.get('backtest_results', {})

        prompt = f"""请分析以下股票回测结果：

**股票信息**
- 代码：{stock_info.get('symbol', 'N/A')}
- 名称：{stock_info.get('name', 'N/A')}
- 回测周期：{stock_info.get('period', 'N/A')}

**策略信息**
- 策略名称：{strategy_info.get('name', 'N/A')}
- 策略描述：{strategy_info.get('description', 'N/A')}

**参数配置**
- 初始资金：{parameters.get('initial_capital', 0):,.0f} 元
- 手续费率：{parameters.get('commission_rate', 0):.4f}
- 策略参数：{parameters.get('strategy_params', {})}

**回测结果**
- 总收益率：{results.get('total_return', 0):.2%}
- 胜率：{results.get('win_rate', 0):.2%}
- 最大回撤：{results.get('max_drawdown', 0):.2%}
- 盈亏比：{results.get('profit_factor', 0):.2f}
- 总交易次数：{results.get('total_trades', 0)}
- 盈利次数：{results.get('winning_trades', 0)}
- 亏损次数：{results.get('losing_trades', 0)}

请根据以上数据，给出专业的分析和建议。"""

        return prompt

    def _call_qwen_api(self, user_prompt: str) -> Dict[str, Any]:
        """调用通义千问API.

        Args:
            user_prompt: 用户提示词

        Returns:
            API响应数据

        Raises:
            requests.exceptions.RequestException: API调用失败
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'input': {
                'messages': [
                    {
                        'role': 'system',
                        'content': self.SYSTEM_PROMPT
                    },
                    {
                        'role': 'user',
                        'content': user_prompt
                    }
                ]
            },
            'parameters': {
                'max_tokens': self.max_tokens,
                'temperature': 0.7,  # 适中的创造性
                'top_p': 0.9
            }
        }

        response = requests.post(
            self.api_url,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )

        response.raise_for_status()
        return response.json()

    def is_configured(self) -> bool:
        """检查服务是否已配置.

        Returns:
            是否已配置API密钥
        """
        return bool(self.api_key)


# 全局单例
_ai_service: Optional[AIAnalysisService] = None


def get_ai_analysis_service() -> AIAnalysisService:
    """获取AI分析服务单例.

    Returns:
        AIAnalysisService实例
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIAnalysisService()
    return _ai_service
