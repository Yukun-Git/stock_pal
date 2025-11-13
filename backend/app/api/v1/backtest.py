"""Backtest-related API endpoints."""

from pathlib import Path
from flask import request
from flask_restful import Resource

from app.services.data_service import DataService
from app.services.cache_service import CacheService
from app.services.indicator_service import IndicatorService
from app.services.strategy_service import StrategyService
from app.services.strategy_combiner import StrategyCombiner
from app.services.signal_analysis_service import SignalAnalysisService

# 新回测引擎
from app.backtest.orchestrator import BacktestOrchestrator
from app.backtest.models import BacktestConfig, StockInfo
from app.backtest.optimization import GridSearchOptimizer


class StrategyListResource(Resource):
    """Resource for getting list of available strategies."""

    def get(self):
        """Get list of all available trading strategies.

        Returns:
            JSON response with strategy list
        """
        try:
            strategies = StrategyService.get_all_strategies()

            return {
                'success': True,
                'data': strategies
            }, 200

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500


class StrategyDocumentationResource(Resource):
    """Resource for getting strategy documentation."""

    def get(self, strategy_id):
        """Get documentation for a specific strategy.

        Args:
            strategy_id: Strategy identifier (e.g., 'ma_cross')

        Returns:
            JSON response with strategy documentation
        """
        try:
            # Get project root directory
            backend_dir = Path(__file__).resolve().parent.parent.parent.parent
            doc_path = backend_dir / 'doc' / 'strategy' / f'{strategy_id}.md'

            # Check if documentation file exists
            if not doc_path.exists():
                return {
                    'success': False,
                    'error': f'Documentation not found for strategy: {strategy_id}'
                }, 404

            # Read documentation content
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Get strategy info
            strategies = StrategyService.get_all_strategies()
            strategy_info = next((s for s in strategies if s['id'] == strategy_id), None)

            return {
                'success': True,
                'data': {
                    'strategy_id': strategy_id,
                    'strategy_name': strategy_info['name'] if strategy_info else strategy_id,
                    'content': content
                }
            }, 200

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500


class BacktestResource(Resource):
    """Resource for running backtests using new engine."""

    def post(self):
        """Run a backtest.

        Request body (JSON):
            Single strategy:
            {
                "symbol": "000001",
                "strategy_id": "ma_cross",
                "start_date": "20220101",
                "end_date": "20241231",
                "initial_capital": 100000,
                "commission_rate": 0.0003,
                "min_commission": 5.0,
                "slippage_bps": 5.0,
                "stamp_tax_rate": 0.001,
                "strategy_params": {...}
            }

            Multiple strategies (combined):
            {
                "symbol": "000001",
                "strategy_ids": ["ma_cross", "macd_cross"],
                "combine_mode": "AND",  // 'AND', 'OR', or 'VOTE'
                "vote_threshold": 2,    // For VOTE mode
                "start_date": "20220101",
                "end_date": "20241231",
                "initial_capital": 100000,
                "commission_rate": 0.0003,
                "strategy_params": {...}
            }

        Returns:
            JSON response with backtest results (enhanced metrics)
        """
        try:
            data = request.get_json()

            # Validate required fields
            if 'symbol' not in data:
                return {
                    'success': False,
                    'error': 'Missing required field: symbol'
                }, 400

            # Support both single and multiple strategies
            if 'strategy_ids' in data:
                strategy_ids = data['strategy_ids']
                if not isinstance(strategy_ids, list) or len(strategy_ids) == 0:
                    return {
                        'success': False,
                        'error': 'strategy_ids must be a non-empty list'
                    }, 400
                combine_mode = data.get('combine_mode', 'AND')
                vote_threshold = data.get('vote_threshold', 2)
            elif 'strategy_id' in data:
                strategy_ids = [data['strategy_id']]
                combine_mode = 'AND'
                vote_threshold = 1
            else:
                return {
                    'success': False,
                    'error': 'Missing required field: strategy_id or strategy_ids'
                }, 400

            symbol = data['symbol']
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            # Get stock data
            stock_info = DataService.get_stock_info(symbol)
            cache_service = CacheService()
            df = cache_service.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )

            # Calculate indicators
            df = IndicatorService.calculate_all_indicators(df)

            # Generate signals
            strategy_params = data.get('strategy_params', {})
            per_strategy_params = data.get('per_strategy_params', {})

            if len(strategy_ids) == 1:
                # Single strategy
                params = per_strategy_params.get(strategy_ids[0], strategy_params)
                df_with_signals = StrategyService.apply_strategy(strategy_ids[0], df, params)
            else:
                # Multiple strategies - combine signals
                signal_columns = []
                for strategy_id in strategy_ids:
                    signal_col = StrategyCombiner.get_strategy_signal_column(strategy_id)
                    df_copy = df.copy()
                    params = per_strategy_params.get(strategy_id, strategy_params)
                    df_copy = StrategyService.apply_strategy(strategy_id, df_copy, params)
                    df[signal_col] = df_copy['signal']
                    signal_columns.append(signal_col)

                df_with_signals = StrategyCombiner.combine_signals(
                    df,
                    signal_columns,
                    combine_mode=combine_mode,
                    vote_threshold=vote_threshold
                )

            # Create backtest config (using new engine)
            config = BacktestConfig(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=data.get('initial_capital', 100000),
                commission_rate=data.get('commission_rate', 0.0003),
                min_commission=data.get('min_commission', 5.0),
                slippage_bps=data.get('slippage_bps', 5.0),
                stamp_tax_rate=data.get('stamp_tax_rate', 0.001),
                strategy_id=strategy_ids[0] if len(strategy_ids) == 1 else 'combined',
                strategy_params=strategy_params
            )

            # Run backtest with new engine
            orchestrator = BacktestOrchestrator(config)

            # Debug: Check environment initialization
            if orchestrator.environment is None:
                raise ValueError("Failed to initialize trading environment")

            # Create stock info for new engine (after orchestrator initializes environment)
            stock_info_obj = StockInfo(
                symbol=symbol,
                name=stock_info['name'],
                board=orchestrator.environment.board
            )

            result = orchestrator.run(
                market_data=df[['date', 'open', 'high', 'low', 'close', 'volume']],
                signals=df_with_signals[['date', 'signal']],
                stock_info=stock_info_obj
            )

            # Convert trades to API format
            trades_api = []
            for trade in result.trades:
                trades_api.append({
                    'date': trade.executed_at.strftime('%Y-%m-%d'),
                    'action': 'buy' if trade.side.value == 'buy' else 'sell',
                    'price': float(trade.price),
                    'shares': int(trade.quantity),
                    'amount': float(trade.amount),
                    'commission': float(trade.commission)
                })

            # Convert equity curve to API format
            equity_curve_api = []
            for _, row in result.equity_curve.iterrows():
                equity_curve_api.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'equity': float(row['equity']),
                    'cash': float(row['cash']),
                    'position_value': float(row['position_value'])
                })

            # Prepare K-line data with signals
            df_with_signals['date'] = df_with_signals['date'].astype(str)
            klines = df_with_signals[['date', 'open', 'high', 'low', 'close', 'volume', 'signal']].to_dict('records')

            # Find buy/sell points
            buy_points = []
            sell_points = []
            for i, row in df_with_signals.iterrows():
                if row['signal'] == 1:
                    buy_points.append({
                        'date': str(row['date']),
                        'price': row['close']
                    })
                elif row['signal'] == -1:
                    sell_points.append({
                        'date': str(row['date']),
                        'price': row['close']
                    })

            # Prepare strategy info
            if len(strategy_ids) == 1:
                strategy_info = strategy_ids[0]
            else:
                strategy_info = {
                    'strategies': strategy_ids,
                    'combine_mode': combine_mode,
                    'vote_threshold': vote_threshold if combine_mode == 'VOTE' else None
                }

            # Analyze current signal proximity
            signal_analysis = None
            try:
                analysis_params = {}
                for strategy_id in strategy_ids:
                    analysis_params[strategy_id] = per_strategy_params.get(strategy_id, strategy_params)

                signal_analysis = SignalAnalysisService.analyze_current_signals(
                    df=df_with_signals,
                    strategy_ids=strategy_ids,
                    per_strategy_params=analysis_params
                )
            except Exception as e:
                print(f"Signal analysis failed: {e}")
                signal_analysis = {
                    "status": "error",
                    "message": f"分析失败: {str(e)}"
                }

            # Build enhanced results using new metrics
            metrics = result.metrics

            return {
                'success': True,
                'data': {
                    'stock': stock_info,
                    'strategy': strategy_info,
                    'results': {
                        # Basic metrics (backward compatible)
                        'initial_capital': config.initial_capital,
                        'final_capital': float(result.equity_curve['equity'].iloc[-1]),
                        'total_return': float(metrics.get('total_return', 0)),
                        'total_trades': int(metrics.get('total_trades', 0)),
                        'win_rate': float(metrics.get('win_rate', 0)),
                        'max_drawdown': float(metrics.get('max_drawdown', 0)),
                        'profit_factor': float(metrics.get('profit_factor', 0)),

                        # Enhanced metrics from new engine
                        'cagr': float(metrics.get('cagr', 0)),
                        'sharpe_ratio': float(metrics.get('sharpe_ratio', 0)),
                        'sortino_ratio': float(metrics.get('sortino_ratio', 0)),
                        'calmar_ratio': float(metrics.get('calmar_ratio', 0)),
                        'volatility': float(metrics.get('volatility', 0)),
                        'max_drawdown_duration': float(metrics.get('max_drawdown_duration', 0)),
                        'turnover_rate': float(metrics.get('turnover_rate', 0)),
                        'avg_holding_period': float(metrics.get('avg_holding_period', 0)),
                        'avg_trade_return': float(metrics.get('avg_trade_return', 0)),

                        # Backward compatibility
                        'winning_trades': int(metrics.get('total_trades', 0) * metrics.get('win_rate', 0) / 100) if metrics.get('win_rate', 0) > 0 else 0,
                        'losing_trades': int(metrics.get('total_trades', 0) * (1 - metrics.get('win_rate', 0) / 100)) if metrics.get('win_rate', 0) > 0 else 0,
                        'avg_profit': float(metrics.get('avg_profit_amount', 0)),
                        'avg_loss': float(metrics.get('avg_loss_amount', 0)),
                    },
                    'trades': trades_api,
                    'equity_curve': equity_curve_api,
                    'klines': klines,
                    'buy_points': buy_points,
                    'sell_points': sell_points,
                    'signal_analysis': signal_analysis,
                    'metadata': result.metadata  # New: backtest metadata
                }
            }, 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }, 500


class BacktestOptimizeResource(Resource):
    """Resource for parameter optimization."""

    def post(self):
        """Run parameter optimization.

        Request body (JSON):
            {
                "symbol": "000001",
                "strategy_id": "ma_cross",
                "start_date": "20220101",
                "end_date": "20241231",
                "initial_capital": 100000,
                "param_grid": {
                    "short_period": [5, 10, 15, 20],
                    "long_period": [30, 60, 90, 120]
                },
                "optimization_metric": "sharpe_ratio",
                "constraints": {
                    "min_sharpe_ratio": 1.0,
                    "max_max_drawdown": -0.20
                }
            }

        Returns:
            JSON response with optimization results
        """
        try:
            data = request.get_json()

            # Validate required fields
            required_fields = ['symbol', 'strategy_id', 'param_grid']
            for field in required_fields:
                if field not in data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, 400

            symbol = data['symbol']
            strategy_id = data['strategy_id']
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            param_grid = data['param_grid']

            # Get stock data
            cache_service = CacheService()
            df = cache_service.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )

            # Calculate indicators
            df = IndicatorService.calculate_all_indicators(df)

            # Create config
            config = BacktestConfig(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=data.get('initial_capital', 100000),
                commission_rate=data.get('commission_rate', 0.0003),
                min_commission=data.get('min_commission', 5.0),
                slippage_bps=data.get('slippage_bps', 5.0),
                stamp_tax_rate=data.get('stamp_tax_rate', 0.001)
            )

            # Get strategy function
            def strategy_func(market_data, params):
                """Wrapper to apply strategy"""
                df_copy = market_data.copy()
                df_copy = IndicatorService.calculate_all_indicators(df_copy)
                df_result = StrategyService.apply_strategy(strategy_id, df_copy, params)
                return df_result[['date', 'signal']]

            # Create optimizer
            optimizer = GridSearchOptimizer(
                config=config,
                param_grid=param_grid,
                optimization_metric=data.get('optimization_metric', 'sharpe_ratio')
            )

            # Run optimization
            result = optimizer.optimize(
                market_data=df,
                strategy_func=strategy_func,
                constraints=data.get('constraints')
            )

            # Convert results to API format
            all_results_api = []
            for item in result.all_results[:100]:  # Limit to 100 results
                all_results_api.append({
                    'params': item['params'],
                    'score': float(item['score']) if item['score'] != float('-inf') else None,
                    'total_return': float(item.get('total_return', 0)),
                    'sharpe_ratio': float(item.get('sharpe_ratio', 0)),
                    'max_drawdown': float(item.get('max_drawdown', 0)),
                    'win_rate': float(item.get('win_rate', 0))
                })

            return {
                'success': True,
                'data': {
                    'best_params': result.best_params,
                    'best_score': float(result.best_score) if result.best_score != float('-inf') else None,
                    'total_combinations': result.total_combinations,
                    'execution_time': result.execution_time_seconds,
                    'all_results': all_results_api,
                    'heatmap_data': result.heatmap_data
                }
            }, 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }, 500
