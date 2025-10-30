"""API v1 routes."""

from flask_restful import Api
from app.api.v1.stocks import StockListResource, StockSearchResource, StockDataResource
from app.api.v1.backtest import BacktestResource, StrategyListResource


def register_routes(api: Api):
    """Register all API v1 routes.

    Args:
        api: Flask-RESTful Api instance
    """
    # Stock routes
    api.add_resource(StockListResource, '/api/v1/stocks')
    api.add_resource(StockSearchResource, '/api/v1/stocks/search')
    api.add_resource(StockDataResource, '/api/v1/stocks/<string:symbol>/data')

    # Backtest routes
    api.add_resource(StrategyListResource, '/api/v1/strategies')
    api.add_resource(BacktestResource, '/api/v1/backtest')
