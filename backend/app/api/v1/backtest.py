"""Backtest-related API endpoints."""

from flask import request
from flask_restful import Resource
from app.services.data_service import DataService
from app.services.indicator_service import IndicatorService
from app.services.strategy_service import StrategyService
from app.services.backtest_service import BacktestService


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


class BacktestResource(Resource):
    """Resource for running backtests."""

    def post(self):
        """Run a backtest.

        Request body (JSON):
            {
                "symbol": "000001",
                "strategy_id": "ma_cross",
                "start_date": "20220101",
                "end_date": "20241231",
                "initial_capital": 100000,
                "commission_rate": 0.0003,
                "strategy_params": {
                    "fast_period": 5,
                    "slow_period": 20
                }
            }

        Returns:
            JSON response with backtest results
        """
        try:
            data = request.get_json()

            # Validate required fields
            required_fields = ['symbol', 'strategy_id']
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
            initial_capital = data.get('initial_capital', 100000)
            commission_rate = data.get('commission_rate', 0.0003)
            strategy_params = data.get('strategy_params', {})

            # Step 1: Get stock data
            stock_info = DataService.get_stock_info(symbol)
            df = DataService.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust='qfq'
            )

            # Step 2: Calculate indicators
            df = IndicatorService.calculate_all_indicators(df)

            # Step 3: Apply strategy
            df = StrategyService.apply_strategy(strategy_id, df, strategy_params)

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

            return {
                'success': True,
                'data': {
                    'stock': stock_info,
                    'strategy': strategy_id,
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
                    'sell_points': sell_points
                }
            }, 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }, 500
