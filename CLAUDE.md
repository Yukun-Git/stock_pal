# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

对于重新构建镜像一定要谨慎，太费时间。大部分时候，能够通过重启服务就能达到目的。
所有的端口设置一定要小心，绝不能和宿主机上的其他服务产生冲突（PORT_INFO.md）。
写详细设计文档的时候，不要包含具体的代码实现，以免文档过长。
目前项目处于早期阶段，所有的详细设计和开发计划都不需要考虑数据迁移之类的内容。

## Project Overview

A full-stack stock backtesting system designed for retail investors in Chinese A-share markets. The system allows users to test trading strategies using historical data and technical indicators.

**Tech Stack:**
- Backend: Flask 3.0 + Flask-RESTful (Python 3.8+)
- Frontend: React 18 + TypeScript + Ant Design 5 + ECharts 5
- Data Source: AkShare (free Chinese A-share market data)
- Deployment: Docker + Docker Compose

## Development Commands

### Docker Operations (Preferred)

The project uses Docker for deployment. Use `make` commands for convenience:

```bash
# Start all services
make up                  # Start services in background
make dev                 # Start with live reload for development
make logs                # View all service logs
make logs-backend        # Backend logs only
make logs-frontend       # Frontend logs only

# Build and rebuild
make build               # Build Docker images
make rebuild             # Full rebuild (no cache) and restart

# Container management
make down                # Stop services
make restart             # Restart services
make ps                  # Show service status
make shell-backend       # Open shell in backend container
make shell-frontend      # Open shell in frontend container

# Testing and code quality (requires running containers)
make test-backend        # Run pytest tests
make lint-backend        # Run flake8 linting
make format-backend      # Format code with Black

# Utilities
make health              # Check service health endpoints
make clean               # Stop and remove containers/networks
make clean-all           # Remove everything including images
```

### Local Development (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py            # Starts Flask dev server on port 4001
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev              # Starts Vite dev server on port 4000
npm run build            # Production build (TypeScript + Vite)
npm run lint             # ESLint checking
npm run preview          # Preview production build
```

## Architecture Overview

### Service-Oriented Backend Design

The backend follows a **layered service architecture** with clear separation of concerns:

1. **API Layer** (`app/api/v1/`): RESTful endpoints, request validation, response formatting
2. **Service Layer** (`app/services/`): Business logic, data processing, strategy execution
3. **Models Layer** (`app/models/`): Data structures and validation

### Key Service Components

**Data Service** (`data_service.py`):
- Fetches historical stock data from AkShare API
- Handles data cleaning and normalization
- Manages date range validation and stock code formatting
- Returns pandas DataFrames with OHLCV data

**Indicator Service** (`indicator_service.py`):
- Calculates technical indicators: MA, EMA, MACD, KDJ, RSI, Bollinger Bands
- All indicators implemented using pandas/numpy for performance
- Each indicator is a pure function: takes DataFrame, returns DataFrame with new columns
- Indicators can be composed (e.g., MACD uses EMA internally)

**Strategy Service** (`strategy_service.py`):
- Defines trading strategies as classes with `generate_signals()` method
- Each strategy returns a DataFrame with `buy_signal` and `sell_signal` columns (boolean)
- Strategies operate on price + indicator data, producing buy/sell signals
- Strategies included: Morning Star, MA Cross, MACD Cross, KDJ Cross, RSI Reversal, Bollinger Breakout

**Backtest Service** (`backtest_service.py`):
- Core backtesting engine that simulates trades
- Takes stock data, signals, and parameters (initial capital, commission rate)
- Tracks position state: `None` (no position) or holding shares
- Calculates trade-by-trade P&L, equity curve, and performance metrics
- Returns: trades list, equity curve, total return, win rate, max drawdown, profit factor

### Data Flow for Backtesting

1. **Request arrives** at `/api/v1/backtest` endpoint (POST)
2. **API layer** validates params: symbol, strategy_id, date range, initial capital, commission rate
3. **Data Service** fetches historical OHLCV data from AkShare
4. **Indicator Service** calculates required technical indicators based on strategy
5. **Strategy Service** generates buy/sell signals from price + indicator data
6. **Backtest Service** simulates trades and calculates performance metrics
7. **API layer** formats and returns results (trades, equity curve, metrics)

### Frontend Architecture

- **Page-based routing**: HomePage (landing), BacktestPage (main interface)
- **Service layer** (`services/api.ts`): Centralized API client using axios
- **Chart components**: KLineChart (candlestick with buy/sell markers), EquityCurveChart (equity over time)
- **State management**: React hooks, no Redux (relatively simple state)

### Docker Deployment Architecture

- **Backend container**: Runs Flask app via Gunicorn (production WSGI server)
- **Frontend container**: Nginx serves static React build + proxies `/api` to backend
- **Network**: Custom bridge network `stock-backtest-network` for inter-container communication
- **Health checks**: Backend exposes `/health` endpoint; both containers have health monitoring
- **Logging**: JSON file driver with rotation (max 10MB, 3 files)

## Technical Details and Conventions

### Backtest Engine Implementation

The backtesting logic follows a **state machine** pattern:
- State: `position = None` (no position) or `position = {'shares': N, 'buy_price': P}`
- On buy signal: If no position, buy as many shares as possible with available capital
- On sell signal: If holding position, sell all shares
- Commission is applied to both buy and sell transactions
- Equity is calculated daily based on position value + remaining cash

### Trading Strategy Interface

All strategies must implement:
```python
class MyStrategy:
    def generate_signals(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Args:
            df: DataFrame with OHLCV + indicators
            params: Strategy-specific parameters
        Returns:
            DataFrame with 'buy_signal' and 'sell_signal' boolean columns
        """
```

### API Versioning

- Current API version: `v1` (routes at `/api/v1/*`)
- When adding new endpoints, maintain backward compatibility
- If breaking changes needed, create new version (`v2`)

### Date Handling

- AkShare expects dates in `YYYYMMDD` format (string, no dashes)
- Frontend sends ISO format, backend converts to AkShare format
- All date ranges are inclusive of start and end dates

### Stock Code Format

- Chinese A-share codes: 6-digit numbers
- Shanghai stocks: Start with `6` (e.g., `600000`)
- Shenzhen stocks: Start with `0` or `3` (e.g., `000001`, `300001`)
- Stock search supports both code and name (Chinese characters)

### Environment Configuration

Backend uses environment-based config classes (`app/config.py`):
- `DevelopmentConfig`: Debug enabled, relaxed CORS
- `ProductionConfig`: Debug disabled, restricted CORS, Gunicorn
- `TestConfig`: Isolated test settings

Set via `FLASK_ENV` environment variable in docker-compose.yml

### Performance Considerations

- AkShare API calls can be slow (external network request)
- Backtests on 2+ years of daily data may take several seconds
- No caching implemented yet (potential future optimization)
- Large stock lists use lazy loading/pagination on frontend

## Important Notes

- **Data freshness**: AkShare provides daily data, typically updated after market close
- **Testing**: Backend tests use pytest; run in Docker container for consistency
- **Code formatting**: Backend uses Black with default settings (88 char line length)
- **Linting**: Backend uses flake8; frontend uses ESLint with TypeScript rules
- **CORS**: Backend allows localhost origins for development; configure for production deployment

## API Endpoints Reference

### Stock Endpoints
- `GET /api/v1/stocks/search?keyword={keyword}` - Search stocks by code or name
- `GET /api/v1/stocks/{symbol}/data?start_date={date}&end_date={date}` - Get historical data

### Backtest Endpoints
- `GET /api/v1/strategies` - List all available strategies
- `POST /api/v1/backtest` - Run backtest (body: symbol, strategy_id, dates, capital, commission, params)

### Health Check
- `GET /health` - Returns `{"status": "ok"}` for container health monitoring
