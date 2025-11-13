"""
回测编排器

协调所有回测模块，执行完整的回测流程
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
import uuid

from .models import (
    BacktestConfig,
    BacktestResult,
    Signal,
    MarketData,
    Portfolio,
    TradingEnvironment,
    StockInfo
)
from .trading_engine import TradingEngine
from .risk_manager import RiskConfig
from .metrics import MetricsCalculator
from .rules.trading_calendar import TradingCalendar
from .rules.symbol_classifier import SymbolClassifier


class BacktestOrchestrator:
    """
    回测编排器

    职责：
    1. 协调各模块执行回测
    2. 管理元数据
    3. 聚合结果
    """

    def __init__(self, config: BacktestConfig, risk_config: Optional[RiskConfig] = None):
        """
        初始化编排器

        Args:
            config: 回测配置
            risk_config: 风控配置（可选）
        """
        self.config = config
        self.risk_config = risk_config
        self.backtest_id = self._generate_backtest_id()

        # 初始化交易日历
        self.calendar = TradingCalendar()

        # 识别交易环境
        self.environment = self._identify_environment()

        # 初始化交易引擎（引擎内部包含撮合引擎和验证器）
        self.trading_engine = TradingEngine(
            environment=self.environment,
            initial_capital=config.initial_capital,
            commission_rate=config.commission_rate,
            min_commission=config.min_commission,
            slippage_bps=config.slippage_bps,
            stamp_tax_rate=config.stamp_tax_rate,
            risk_config=risk_config  # 传递风控配置
        )

        # 指标计算器
        self.metrics_calculator = MetricsCalculator()

        # 元数据记录
        self.metadata = {
            'backtest_id': self.backtest_id,
            'engine_version': config.engine_version,
            'environment': str(self.environment),
            'started_at': datetime.now().isoformat(),
            'risk_enabled': risk_config is not None
        }

    def _generate_backtest_id(self) -> str:
        """生成回测ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"bt_{timestamp}_{unique_id}"

    def _identify_environment(self) -> TradingEnvironment:
        """
        识别交易环境

        根据股票代码自动识别市场和板块
        """
        if self.config.trading_environment:
            return self.config.trading_environment

        # 自动识别板块 (返回 tuple: market, board)
        market, board = SymbolClassifier.classify(self.config.symbol)

        # 构建交易环境
        return TradingEnvironment(
            market=market,
            board=board,
            channel='DIRECT'
        )

    def run(
        self,
        market_data: pd.DataFrame,
        signals: pd.DataFrame,
        stock_info: Optional[StockInfo] = None
    ) -> BacktestResult:
        """
        运行回测

        Args:
            market_data: 市场数据 (OHLCV)，必须包含列：
                - date: 日期
                - open, high, low, close, volume: OHLCV数据
                - prev_close: 昨收价（用于涨跌停计算）
            signals: 交易信号，必须包含列：
                - date: 日期
                - signal: 信号 (1=买入, -1=卖出, 0=持有)
            stock_info: 股票信息（可选）

        Returns:
            BacktestResult: 回测结果
        """
        # 记录开始时间
        start_time = datetime.now()

        # 合并数据
        df = self._prepare_data(market_data, signals)

        # 如果没有提供股票信息，创建一个默认的
        if stock_info is None:
            stock_info = StockInfo(
                symbol=self.config.symbol,
                name=self.config.symbol,
                board=self.environment.board
            )

        # 逐日回测循环
        equity_records = []
        for idx, row in df.iterrows():
            current_date = row['date']

            # 检查是否为交易日
            if not self.calendar.is_trading_day(current_date):
                continue

            # 构建市场数据
            market_data_obj = MarketData(
                symbol=self.config.symbol,
                date=current_date,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                prev_close=row['prev_close'],
                is_suspended=row.get('is_suspended', False),
                board_type=self.environment.board,
                stock_name=stock_info.name
            )

            # 处理信号（如果有）
            signal_value = row.get('signal', 0)
            signal = Signal(
                symbol=self.config.symbol,
                date=current_date,
                action=int(signal_value),
                price=market_data_obj.close,
                reason=row.get('signal_reason', None)
            )

            # 交易引擎处理信号（内部会进行验证、撮合、更新持仓）
            self.trading_engine.process_signal(
                signal=signal,
                market_data=market_data_obj,
                current_date=current_date
            )

            # 记录当日权益（从交易引擎的历史记录中获取）
            equity_records.append({
                'date': current_date,
                'equity': self.trading_engine.portfolio.total_equity,
                'cash': self.trading_engine.portfolio.cash,
                'position_value': self.trading_engine.portfolio.market_value
            })

        # 构建权益曲线DataFrame
        equity_curve_df = pd.DataFrame(equity_records)

        # 将 DataFrame 转换为 Series（用于指标计算）
        equity_curve_series = equity_curve_df.set_index('date')['equity']

        # 计算性能指标
        metrics = self.metrics_calculator.calculate_all_metrics(
            equity_curve=equity_curve_series,
            trades=self.trading_engine.trades
        )

        # 记录结束时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 更新元数据
        self.metadata.update({
            'completed_at': end_time.isoformat(),
            'execution_time_seconds': execution_time,
            'data_points': len(df),
            'trading_days': len(equity_records),
            'total_orders': len(self.trading_engine.orders),
            'total_trades': len(self.trading_engine.trades),
        })

        # 如果启用了风控，添加风控统计
        if self.risk_config is not None:
            risk_stats = self.trading_engine.get_risk_stats()
            self.metadata['risk_stats'] = risk_stats['risk_stats']
            self.metadata['risk_events'] = risk_stats['risk_events']

        # 构建结果
        result = BacktestResult(
            config=self.config,
            trades=self.trading_engine.trades,
            equity_curve=equity_curve_df,
            metrics=metrics,
            metadata=self.metadata,
            created_at=start_time
        )

        return result

    def _prepare_data(
        self,
        market_data: pd.DataFrame,
        signals: pd.DataFrame
    ) -> pd.DataFrame:
        """
        准备数据

        合并市场数据和信号数据

        Args:
            market_data: 市场数据
            signals: 交易信号

        Returns:
            合并后的DataFrame
        """
        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(market_data['date']):
            market_data = market_data.copy()
            market_data['date'] = pd.to_datetime(market_data['date'])

        if not pd.api.types.is_datetime64_any_dtype(signals['date']):
            signals = signals.copy()
            signals['date'] = pd.to_datetime(signals['date'])

        # 合并数据
        df = pd.merge(
            market_data,
            signals,
            on='date',
            how='left'
        )

        # 填充缺失的信号为0
        df['signal'] = df['signal'].fillna(0)

        # 按日期排序
        df = df.sort_values('date').reset_index(drop=True)

        # 计算prev_close（如果没有）
        if 'prev_close' not in df.columns:
            df['prev_close'] = df['close'].shift(1)
            # 第一天使用当天收盘价
            df.loc[0, 'prev_close'] = df.loc[0, 'close']

        return df

    def run_with_strategy(
        self,
        market_data: pd.DataFrame,
        strategy_func,
        strategy_params: Optional[Dict[str, Any]] = None,
        stock_info: Optional[StockInfo] = None
    ) -> BacktestResult:
        """
        使用策略函数运行回测

        Args:
            market_data: 市场数据
            strategy_func: 策略函数，接受 (DataFrame, params) -> DataFrame with signals
            strategy_params: 策略参数
            stock_info: 股票信息

        Returns:
            BacktestResult: 回测结果
        """
        # 应用策略生成信号
        if strategy_params is None:
            strategy_params = {}

        signals_df = strategy_func(market_data, strategy_params)

        # 运行回测
        return self.run(
            market_data=market_data,
            signals=signals_df,
            stock_info=stock_info
        )
