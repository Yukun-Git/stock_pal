"""Services module."""

from app.services.data_service import DataService
from app.services.indicator_service import IndicatorService
from app.services.strategy_service import StrategyService
from app.services.backtest_service import BacktestService
from app.services.watchlist_service import WatchlistService
from app.services.watchlist_group_service import WatchlistGroupService
from app.services.failover_service import FailoverService, get_failover_service

__all__ = [
    'DataService',
    'IndicatorService',
    'StrategyService',
    'BacktestService',
    'WatchlistService',
    'WatchlistGroupService',
    'FailoverService',
    'get_failover_service',
]
