"""Backtest-related API endpoints."""

import os
from pathlib import Path
from flask import request
from flask_restful import Resource
from app.services.data_service import DataService
from app.services.cache_service import CacheService
from app.services.indicator_service import IndicatorService
from app.services.strategy_service import StrategyService
from app.services.backtest_service import BacktestService
from app.services.strategy_combiner import StrategyCombiner
from app.services.signal_analysis_service import SignalAnalysisService


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
            # Assuming backend/ is at project root
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
    """Resource for running backtests."""

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
                "strategy_params": {...}
            }

            Multiple strategies:
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
            JSON response with backtest results
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
                # Multiple strategies
                strategy_ids = data['strategy_ids']
                if not isinstance(strategy_ids, list) or len(strategy_ids) == 0:
                    return {
                        'success': False,
                        'error': 'strategy_ids must be a non-empty list'
                    }, 400
                combine_mode = data.get('combine_mode', 'AND')
                vote_threshold = data.get('vote_threshold', 2)
            elif 'strategy_id' in data:
                # Single strategy (backward compatibility)
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
            initial_capital = data.get('initial_capital', 100000)
            commission_rate = data.get('commission_rate', 0.0003)

            # Support both unified params and per-strategy params
            strategy_params = data.get('strategy_params', {})
            # New format: {"ma_cross": {...}, "macd_cross": {...}}
            per_strategy_params = data.get('per_strategy_params', {})

            # Step 1: Get stock data (with caching)
            stock_info = DataService.get_stock_info(symbol)
            cache_service = CacheService()
            df = cache_service.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )

            # Step 2: Calculate indicators
            df = IndicatorService.calculate_all_indicators(df)

            # Step 3: Apply strategies
            if len(strategy_ids) == 1:
                # Single strategy - use original logic
                # Try per-strategy params first, fallback to unified params
                params = per_strategy_params.get(strategy_ids[0], strategy_params)
                df = StrategyService.apply_strategy(strategy_ids[0], df, params)
            else:
                # Multiple strategies - generate signals for each
                signal_columns = []
                for strategy_id in strategy_ids:
                    signal_col = StrategyCombiner.get_strategy_signal_column(strategy_id)
                    df_copy = df.copy()
                    # Use per-strategy params if available, fallback to unified params
                    params = per_strategy_params.get(strategy_id, strategy_params)
                    df_copy = StrategyService.apply_strategy(strategy_id, df_copy, params)
                    df[signal_col] = df_copy['signal']
                    signal_columns.append(signal_col)

                # Combine signals
                df = StrategyCombiner.combine_signals(
                    df,
                    signal_columns,
                    combine_mode=combine_mode,
                    vote_threshold=vote_threshold
                )

            # Step 4: Run backtest
            backtest_engine = BacktestService(
                initial_capital=initial_capital,
                commission_rate=commission_rate
            )
            results = backtest_engine.run_backtest(df)

            # Step 5: Prepare response data
            # Convert dates to strings for JSON serialization
            for trade in results['trades']:
                trade['date'] = str(trade['date'])

            for point in results['equity_curve']:
                point['date'] = str(point['date'])

            # Add K-line data with signals for charting
            df['date'] = df['date'].astype(str)
            klines = df[['date', 'open', 'high', 'low', 'close', 'volume', 'signal']].to_dict('records')

            # Find buy/sell points for chart annotation
            buy_points = []
            sell_points = []
            for i, row in df.iterrows():
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

            # Step 6: Analyze current signal proximity
            signal_analysis = None
            try:
                # Build per_strategy_params dict for analysis
                analysis_params = {}
                for strategy_id in strategy_ids:
                    analysis_params[strategy_id] = per_strategy_params.get(strategy_id, strategy_params)

                signal_analysis = SignalAnalysisService.analyze_current_signals(
                    df=df,
                    strategy_ids=strategy_ids,
                    per_strategy_params=analysis_params
                )
            except Exception as e:
                # If analysis fails, log but don't break the response
                print(f"Signal analysis failed: {e}")
                signal_analysis = {
                    "status": "error",
                    "message": f"分析失败: {str(e)}"
                }

            return {
                'success': True,
                'data': {
                    'stock': stock_info,
                    'strategy': strategy_info,
                    'results': {
                        'initial_capital': results['initial_capital'],
                        'final_capital': results['final_capital'],
                        'total_return': results['total_return'],
                        'total_trades': results['total_trades'],
                        'winning_trades': results['winning_trades'],
                        'losing_trades': results['losing_trades'],
                        'win_rate': results['win_rate'],
                        'max_drawdown': results['max_drawdown'],
                        'avg_profit': results['avg_profit'],
                        'avg_loss': results['avg_loss'],
                        'profit_factor': results['profit_factor']
                    },
                    'trades': results['trades'],
                    'equity_curve': results['equity_curve'],
                    'klines': klines,
                    'buy_points': buy_points,
                    'sell_points': sell_points,
                    'signal_analysis': signal_analysis
                }
            }, 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }, 500
