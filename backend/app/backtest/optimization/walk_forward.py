"""
走步验证器

防止策略过拟合的验证方法
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import logging

from ..models import BacktestConfig, BacktestResult
from ..orchestrator import BacktestOrchestrator
from .grid_search import GridSearchOptimizer, GridSearchResult

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardPeriod:
    """
    单个走步验证周期

    包含训练期和测试期的结果
    """
    period_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_best_params: Dict[str, Any]
    train_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    train_result: Optional[BacktestResult] = None
    test_result: Optional[BacktestResult] = None

    def get_degradation(self, metric: str = 'sharpe_ratio') -> float:
        """计算测试期相对训练期的衰减"""
        train_val = self.train_metrics.get(metric, 0)
        test_val = self.test_metrics.get(metric, 0)

        if train_val == 0:
            return 0.0

        return (test_val - train_val) / train_val

    def __repr__(self) -> str:
        train_sharpe = self.train_metrics.get('sharpe_ratio', 0)
        test_sharpe = self.test_metrics.get('sharpe_ratio', 0)
        return (f"WalkForwardPeriod(id={self.period_id}, "
                f"train_sharpe={train_sharpe:.2f}, "
                f"test_sharpe={test_sharpe:.2f})")


@dataclass
class WalkForwardResult:
    """
    走步验证完整结果
    """
    periods: List[WalkForwardPeriod] = field(default_factory=list)
    overall_metrics: Dict[str, float] = field(default_factory=dict)
    is_overfitting: bool = False
    total_periods: int = 0
    execution_time_seconds: float = 0.0

    def __repr__(self) -> str:
        avg_degradation = self.overall_metrics.get('avg_degradation', 0)
        return (f"WalkForwardResult(periods={self.total_periods}, "
                f"overfit={self.is_overfitting}, "
                f"degradation={avg_degradation:.2%})")


class WalkForwardValidator:
    """
    走步验证器

    使用滚动窗口方法验证策略：
    1. 在训练期优化参数
    2. 在测试期验证优化后的参数
    3. 重复多个时间段
    4. 分析训练期与测试期的性能差异
    """

    def __init__(
        self,
        config: BacktestConfig,
        train_period_months: int = 12,
        test_period_months: int = 3,
        step_months: int = 3,
        optimization_metric: str = 'sharpe_ratio'
    ):
        """
        初始化走步验证器

        Args:
            config: 回测配置
            train_period_months: 训练期长度（月）
            test_period_months: 测试期长度（月）
            step_months: 步进长度（月）
            optimization_metric: 优化指标
        """
        self.config = config
        self.train_period_months = train_period_months
        self.test_period_months = test_period_months
        self.step_months = step_months
        self.optimization_metric = optimization_metric

        logger.info(
            f"WalkForwardValidator initialized: "
            f"train={train_period_months}m, test={test_period_months}m, "
            f"step={step_months}m"
        )

    def validate(
        self,
        market_data: pd.DataFrame,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        optimize_in_train: bool = True
    ) -> WalkForwardResult:
        """
        执行走步验证

        Args:
            market_data: 完整的市场数据
            strategy_func: 策略函数
            param_grid: 参数网格（用于优化）
            optimize_in_train: 是否在训练期优化参数

        Returns:
            WalkForwardResult: 验证结果
        """
        import time
        start_time = time.time()

        # 生成时间段划分
        periods_config = self._generate_periods(market_data)

        logger.info(f"Generated {len(periods_config)} walk-forward periods")

        # 对每个时间段进行训练和测试
        periods = []
        for i, period_cfg in enumerate(periods_config):
            logger.info(
                f"Processing period {i+1}/{len(periods_config)}: "
                f"train={period_cfg['train_start']} to {period_cfg['train_end']}, "
                f"test={period_cfg['test_start']} to {period_cfg['test_end']}"
            )

            period_result = self._validate_period(
                market_data,
                strategy_func,
                param_grid,
                period_cfg,
                i + 1,
                optimize_in_train
            )

            if period_result:
                periods.append(period_result)

        # 计算整体指标
        overall_metrics = self._calculate_overall_metrics(periods)

        # 判断是否过拟合
        avg_degradation = overall_metrics.get('avg_degradation', 0)
        is_overfitting = avg_degradation < -0.3  # 测试期性能下降超过30%

        execution_time = time.time() - start_time

        logger.info(
            f"Walk-forward validation completed: "
            f"{len(periods)} periods, "
            f"avg_degradation={avg_degradation:.2%}, "
            f"overfit={is_overfitting}, "
            f"time={execution_time:.2f}s"
        )

        return WalkForwardResult(
            periods=periods,
            overall_metrics=overall_metrics,
            is_overfitting=is_overfitting,
            total_periods=len(periods),
            execution_time_seconds=execution_time
        )

    def _generate_periods(
        self,
        market_data: pd.DataFrame
    ) -> List[Dict[str, str]]:
        """
        生成走步验证的时间段划分

        Returns:
            List of period configs:
            [
                {
                    'train_start': '20200101',
                    'train_end': '20201231',
                    'test_start': '20210101',
                    'test_end': '20210331'
                },
                ...
            ]
        """
        # 获取数据的开始和结束日期
        min_date = pd.to_datetime(market_data['date'].min())
        max_date = pd.to_datetime(market_data['date'].max())

        periods = []
        current_start = min_date

        while True:
            # 计算训练期结束日期
            train_end = current_start + timedelta(days=self.train_period_months * 30)

            # 计算测试期结束日期
            test_end = train_end + timedelta(days=self.test_period_months * 30)

            # 如果测试期超出数据范围，结束
            if test_end > max_date:
                break

            # 添加周期配置
            periods.append({
                'train_start': current_start.strftime('%Y%m%d'),
                'train_end': train_end.strftime('%Y%m%d'),
                'test_start': (train_end + timedelta(days=1)).strftime('%Y%m%d'),
                'test_end': test_end.strftime('%Y%m%d')
            })

            # 步进到下一个周期
            current_start = current_start + timedelta(days=self.step_months * 30)

        return periods

    def _validate_period(
        self,
        market_data: pd.DataFrame,
        strategy_func: Callable,
        param_grid: Dict[str, List[Any]],
        period_cfg: Dict[str, str],
        period_id: int,
        optimize_in_train: bool
    ) -> Optional[WalkForwardPeriod]:
        """验证单个时间段"""
        try:
            # 分割训练和测试数据
            train_data = self._filter_data_by_date(
                market_data,
                period_cfg['train_start'],
                period_cfg['train_end']
            )
            test_data = self._filter_data_by_date(
                market_data,
                period_cfg['test_start'],
                period_cfg['test_end']
            )

            if len(train_data) == 0 or len(test_data) == 0:
                logger.warning(f"Insufficient data for period {period_id}")
                return None

            # 训练期：优化参数
            if optimize_in_train and param_grid:
                train_config = self._create_period_config(
                    period_cfg['train_start'],
                    period_cfg['train_end']
                )

                optimizer = GridSearchOptimizer(
                    train_config,
                    param_grid,
                    self.optimization_metric
                )

                grid_result = optimizer.optimize(train_data, strategy_func)
                best_params = grid_result.best_params
                train_result = grid_result.best_result
                train_metrics = train_result.metrics
            else:
                # 不优化，使用默认参数
                best_params = self.config.strategy_params or {}
                train_config = self._create_period_config(
                    period_cfg['train_start'],
                    period_cfg['train_end']
                )
                orchestrator = BacktestOrchestrator(train_config)
                train_result = orchestrator.run_with_strategy(
                    train_data,
                    strategy_func,
                    best_params
                )
                train_metrics = train_result.metrics

            # 测试期：使用训练期最优参数
            test_config = self._create_period_config(
                period_cfg['test_start'],
                period_cfg['test_end']
            )
            test_orchestrator = BacktestOrchestrator(test_config)
            test_result = test_orchestrator.run_with_strategy(
                test_data,
                strategy_func,
                best_params
            )
            test_metrics = test_result.metrics

            return WalkForwardPeriod(
                period_id=period_id,
                train_start=period_cfg['train_start'],
                train_end=period_cfg['train_end'],
                test_start=period_cfg['test_start'],
                test_end=period_cfg['test_end'],
                train_best_params=best_params,
                train_metrics=train_metrics,
                test_metrics=test_metrics,
                train_result=train_result,
                test_result=test_result
            )

        except Exception as e:
            logger.error(f"Error validating period {period_id}: {e}")
            return None

    def _filter_data_by_date(
        self,
        data: pd.DataFrame,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """按日期过滤数据"""
        df = data.copy()

        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])

        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        return df[(df['date'] >= start) & (df['date'] <= end)].reset_index(drop=True)

    def _create_period_config(
        self,
        start_date: str,
        end_date: str
    ) -> BacktestConfig:
        """创建周期配置"""
        return BacktestConfig(
            symbol=self.config.symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.config.initial_capital,
            commission_rate=self.config.commission_rate,
            min_commission=self.config.min_commission,
            slippage_bps=self.config.slippage_bps,
            stamp_tax_rate=self.config.stamp_tax_rate
        )

    def _calculate_overall_metrics(
        self,
        periods: List[WalkForwardPeriod]
    ) -> Dict[str, float]:
        """计算整体指标"""
        if not periods:
            return {}

        # 收集所有训练期和测试期指标
        train_sharpes = [p.train_metrics.get('sharpe_ratio', 0) for p in periods]
        test_sharpes = [p.test_metrics.get('sharpe_ratio', 0) for p in periods]

        train_returns = [p.train_metrics.get('total_return', 0) for p in periods]
        test_returns = [p.test_metrics.get('total_return', 0) for p in periods]

        # 计算衰减
        degradations = [p.get_degradation('sharpe_ratio') for p in periods]

        return {
            'avg_train_sharpe': sum(train_sharpes) / len(train_sharpes),
            'avg_test_sharpe': sum(test_sharpes) / len(test_sharpes),
            'avg_train_return': sum(train_returns) / len(train_returns),
            'avg_test_return': sum(test_returns) / len(test_returns),
            'avg_degradation': sum(degradations) / len(degradations),
            'min_test_sharpe': min(test_sharpes),
            'max_test_sharpe': max(test_sharpes)
        }
