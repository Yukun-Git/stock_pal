"""API v1 routes."""

from flask_restful import Api
from app.api.v1.stocks import StockListResource, StockSearchResource, StockDataResource
from app.api.v1.backtest import (
    BacktestResource,
    StrategyListResource,
    StrategyDocumentationResource,
    BacktestOptimizeResource,
    BenchmarkListResource
)
from app.api.v1.watchlist import (
    WatchlistResource,
    WatchlistItemResource,
    WatchlistBatchResource,
    WatchlistCheckResource
)
from app.api.v1.watchlist_groups import (
    WatchlistGroupsResource,
    WatchlistGroupResource
)
from app.api.v1.adapters import (
    AdapterListResource,
    AdapterStatusResource,
    AdapterHealthResource,
    AdapterMetricsResource
)


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
    api.add_resource(StrategyDocumentationResource, '/api/v1/strategies/<string:strategy_id>/documentation')
    api.add_resource(BacktestResource, '/api/v1/backtest')
    api.add_resource(BacktestOptimizeResource, '/api/v1/backtest/optimize')
    api.add_resource(BenchmarkListResource, '/api/v1/benchmarks')

    # Watchlist routes
    api.add_resource(WatchlistResource, '/api/v1/watchlist')
    api.add_resource(WatchlistItemResource, '/api/v1/watchlist/<int:stock_id>')
    api.add_resource(WatchlistBatchResource, '/api/v1/watchlist/batch')
    api.add_resource(WatchlistCheckResource, '/api/v1/watchlist/check/<string:stock_code>')

    # Watchlist groups routes
    api.add_resource(WatchlistGroupsResource, '/api/v1/watchlist/groups')
    api.add_resource(WatchlistGroupResource, '/api/v1/watchlist/groups/<int:group_id>')

    # Adapter routes
    api.add_resource(AdapterListResource, '/api/v1/adapters')
    api.add_resource(AdapterStatusResource, '/api/v1/adapters/status')
    api.add_resource(AdapterHealthResource, '/api/v1/adapters/health')
    api.add_resource(AdapterMetricsResource, '/api/v1/adapters/metrics', '/api/v1/adapters/metrics/<string:name>')
