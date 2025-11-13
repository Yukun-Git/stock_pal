"""
参数网格搜索优化器

对策略参数进行网格搜索，找到最优参数组合
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from itertools import product
import pandas as pd
import logging

from ..models import BacktestConfig, BacktestResult
from ..orchestrator import BacktestOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class GridSearchResult:
    """
    网格搜索结果

    包含最佳参数、所有结果和热力图数据
    """
    best_params: Dict[str, Any]
    best_score: float
    best_result: BacktestResult
    all_results: List[Dict[str, Any]] = field(default_factory=list)
    heatmap_data: Optional[Dict[str, Any]] = None
    total_combinations: int = 0
    execution_time_seconds: float = 0.0

    def __repr__(self) -> str:
        return (f"GridSearchResult(best_score={self.best_score:.4f}, "
                f"best_params={self.best_params}, "
                f"total={self.total_combinations})")


class GridSearchOptimizer:
    """
    参数网格搜索优化器

    对给定的参数空间进行穷举搜索，找到最优参数组合
    """

    def __init__(
        self,
        config: BacktestConfig,
        param_grid: Dict[str, List[Any]],
        optimization_metric: str = 'sharpe_ratio'
    ):
        """
        初始化优化器

        Args:
            config: 回测配置（不含策略参数）
            param_grid: 参数网格，例如:
                {
                    'short_period': [5, 10, 15, 20],
                    'long_period': [30, 60, 90, 120]
                }
            optimization_metric: 优化目标指标，默认 sharpe_ratio
                可选: sharpe_ratio, calmar_ratio, total_return, etc.
        """
        self.config = config
        self.param_grid = param_grid
        self.optimization_metric = optimization_metric

        # 验证参数网格
        self._validate_param_grid()

        logger.info(
            f"GridSearchOptimizer initialized: "
            f"metric={optimization_metric}, "
            f"grid_size={self.get_total_combinations()}"
        )

    def _validate_param_grid(self):
        """验证参数网格"""
        if not self.param_grid:
            raise ValueError("param_grid cannot be empty")

        for param_name, values in self.param_grid.items():
            if not isinstance(values, list):
                raise ValueError(f"param_grid['{param_name}'] must be a list")
            if len(values) == 0:
                raise ValueError(f"param_grid['{param_name}'] cannot be empty")

    def get_total_combinations(self) -> int:
        """计算总的参数组合数"""
        total = 1
        for values in self.param_grid.values():
            total *= len(values)
        return total

    def optimize(
        self,
        market_data: pd.DataFrame,
        strategy_func: Callable,
        constraints: Optional[Dict[str, float]] = None,
        max_workers: int = 1
    ) -> GridSearchResult:
        """
        执行网格搜索优化

        Args:
            market_data: 市场数据
            strategy_func: 策略函数 (data, params) -> signals
            constraints: 约束条件，例如:
                {
                    'min_sharpe': 1.0,
                    'max_drawdown': -0.20
                }
            max_workers: 并行工作数（暂不支持）

        Returns:
            GridSearchResult: 优化结果
        """
        import time
        start_time = time.time()

        # 生成所有参数组合
        param_combinations = self._generate_combinations()
        total_combinations = len(param_combinations)

        logger.info(f"Starting grid search: {total_combinations} combinations")

        # 运行所有组合
        all_results = []
        best_score = float('-inf')
        best_params = None
        best_result = None

        for i, params in enumerate(param_combinations):
            try:
                # 运行回测
                result = self._run_single_backtest(
                    market_data,
                    strategy_func,
                    params
                )

                # 获取优化指标得分
                score = result.metrics.get(self.optimization_metric, float('-inf'))

                # 检查约束条件
                if constraints and not self._check_constraints(result.metrics, constraints):
                    logger.debug(f"Params {params} failed constraints")
                    score = float('-inf')

                # 记录结果
                result_dict = {
                    'params': params,
                    'score': score,
                    **{k: v for k, v in result.metrics.items()}  # 所有指标
                }
                all_results.append(result_dict)

                # 更新最佳结果
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result

                # 进度日志
                if (i + 1) % max(1, total_combinations // 10) == 0:
                    progress = (i + 1) / total_combinations * 100
                    logger.info(
                        f"Progress: {i+1}/{total_combinations} ({progress:.1f}%), "
                        f"current best: {best_score:.4f}"
                    )

            except Exception as e:
                logger.error(f"Error in backtest with params {params}: {e}")
                # 记录失败的结果
                all_results.append({
                    'params': params,
                    'score': float('-inf'),
                    'error': str(e)
                })

        # 生成热力图数据（仅支持2参数）
        heatmap_data = None
        if len(self.param_grid) == 2:
            heatmap_data = self._generate_heatmap_data(all_results)

        execution_time = time.time() - start_time

        logger.info(
            f"Grid search completed: "
            f"best_score={best_score:.4f}, "
            f"best_params={best_params}, "
            f"time={execution_time:.2f}s"
        )

        return GridSearchResult(
            best_params=best_params,
            best_score=best_score,
            best_result=best_result,
            all_results=all_results,
            heatmap_data=heatmap_data,
            total_combinations=total_combinations,
            execution_time_seconds=execution_time
        )

    def _generate_combinations(self) -> List[Dict[str, Any]]:
        """生成所有参数组合"""
        param_names = list(self.param_grid.keys())
        param_values = [self.param_grid[name] for name in param_names]

        combinations = []
        for values in product(*param_values):
            params = dict(zip(param_names, values))
            combinations.append(params)

        return combinations

    def _run_single_backtest(
        self,
        market_data: pd.DataFrame,
        strategy_func: Callable,
        params: Dict[str, Any]
    ) -> BacktestResult:
        """运行单次回测"""
        # 创建新的配置（包含策略参数）
        config = BacktestConfig(
            symbol=self.config.symbol,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_capital=self.config.initial_capital,
            commission_rate=self.config.commission_rate,
            min_commission=self.config.min_commission,
            slippage_bps=self.config.slippage_bps,
            stamp_tax_rate=self.config.stamp_tax_rate,
            strategy_params=params
        )

        # 创建编排器并运行
        orchestrator = BacktestOrchestrator(config)
        result = orchestrator.run_with_strategy(
            market_data,
            strategy_func,
            params
        )

        return result

    def _check_constraints(
        self,
        metrics: Dict[str, float],
        constraints: Dict[str, float]
    ) -> bool:
        """检查是否满足约束条件"""
        for constraint_name, constraint_value in constraints.items():
            metric_name = constraint_name.replace('min_', '').replace('max_', '')

            if metric_name not in metrics:
                logger.warning(f"Constraint metric '{metric_name}' not found in results")
                continue

            metric_value = metrics[metric_name]

            if constraint_name.startswith('min_'):
                if metric_value < constraint_value:
                    return False
            elif constraint_name.startswith('max_'):
                if metric_value > constraint_value:
                    return False

        return True

    def _generate_heatmap_data(
        self,
        all_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成热力图数据（仅支持2个参数）

        Returns:
            {
                'x_param': 'short_period',
                'x_values': [5, 10, 15, 20],
                'y_param': 'long_period',
                'y_values': [30, 60, 90, 120],
                'z_values': [[0.85, 1.25, 0.95, 0.75], ...]  # 得分矩阵
            }
        """
        if len(self.param_grid) != 2:
            return None

        param_names = list(self.param_grid.keys())
        x_param = param_names[0]
        y_param = param_names[1]

        x_values = sorted(self.param_grid[x_param])
        y_values = sorted(self.param_grid[y_param])

        # 创建得分矩阵
        z_values = []
        for y_val in y_values:
            row = []
            for x_val in x_values:
                # 查找对应参数组合的得分
                score = None
                for result in all_results:
                    params = result['params']
                    if params[x_param] == x_val and params[y_param] == y_val:
                        score = result['score']
                        break

                # 如果得分为负无穷，设为None（表示无效）
                if score == float('-inf'):
                    score = None

                row.append(score)
            z_values.append(row)

        return {
            'x_param': x_param,
            'x_values': x_values,
            'y_param': y_param,
            'y_values': y_values,
            'z_values': z_values
        }
