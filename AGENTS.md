# AGENTS.md

This file provides guidance to Qoder (qoder.com) when working with code in this repository.

所有端口相关配置都要先参考 PORT_INFO.md，确保与现有服务不冲突。
写详细设计文档的时候，不要包含具体的代码实现，以免文档过长。
目前项目处于早期阶段，所有的详细设计和开发计划都不需要考虑数据迁移之类的内容。
如果想创建一些临时性的脚本，用于做一些测试，先去看看backend/debug_scripts目录下有没有现成的。如果没有，新创建的测试脚本也要放到backend/debug_scripts目录下。
对于重新构建镜像一定要谨慎，太费时间。大部分时候，能够通过重启服务就能达到目的（`make restart-backend` 或 `make restart-frontend`）。

## Project Structure & Module Organization

`backend/app` hosts the Flask stack: `api/v1` exposes REST resources, `services` implements data, indicator, strategy, and backtest logic, and `utils`/`models` provide shared helpers beside the `run.py` entrypoint. React code stays in `frontend/src` (`pages`, `components`, `services/api.ts`, `types`). Root automation relies on `Makefile` plus `docker-compose.yml`; supporting docs live in `doc/` and cacheable datasets belong in `data/`.

### Backend Architecture (Layered Service Pattern)

**API Layer** (`app/api/v1/`): RESTful endpoints handle request validation and response formatting. All routes registered via `register_routes()` in `app/api/v1/__init__.py`.

**Service Layer** (`app/services/`): Business logic isolated from API layer.
- `data_service.py`: Fetches OHLCV data from configured adapter (AkShare, yFinance, BaoStock)
- `indicator_service.py`: Pure functions calculating technical indicators (MA, MACD, KDJ, RSI, BOLL)
- `strategy_service.py`: Manages strategy registry and execution
- `backtest_service.py`: Legacy simple backtester (deprecated, prefer `BacktestOrchestrator`)
- `cache_service.py`: Multi-tier caching (memory + file)
- `failover_service.py`: Automatic failover between data adapters
- `auth_service.py`: User authentication with bcrypt + JWT
- `watchlist_service.py` / `watchlist_group_service.py`: Watchlist management with PostgreSQL

**Backtest Engine** (`app/backtest/`): Production-grade backtesting system.
- `orchestrator.py`: Coordinates backtest execution; entry point for new backtests
- `trading_engine.py`: State machine managing positions, orders, and equity
- `matching_engine.py`: Simulates order execution with slippage and limit price validation
- `risk_manager.py`: Pre-trade risk checks (position limits, drawdown thresholds, daily loss limits)
- `metrics.py`: Calculates Sharpe ratio, max drawdown, win rate, profit factor, Sortino, Calmar
- `rules/`: Trading calendar, symbol classifier (A-share market/board detection), lot size rules, validator

**Strategy System** (`app/strategies/`):
- `base.py`: `BaseStrategy` abstract class defining `generate_signals(df, params) -> DataFrame`
- `registry.py`: Centralizes all strategies; auto-discovery via decorators
- `indicator/`: Indicator-based strategies (MA cross, MACD cross, KDJ, RSI, BOLL breakout)
- `pattern/`: Pattern recognition strategies (morning star candlestick)
- All strategies must define: `strategy_id`, `name`, `description`, `category`, `get_parameters()`

**Data Adapter System** (`app/adapters/`):
- `base.py`: `BaseDataAdapter` abstract class with `get_stock_data()`, `search_stock()`, `health_check()`
- `akshare_adapter.py`, `yfinance_adapter.py`, `baostock_adapter.py`: Concrete implementations
- `factory.py`: Creates adapters based on config (`DATA_SOURCE` env var)
- `registry.py`: Tracks all registered adapters and their health status
- `failover_service.py`: Automatically switches adapters on failure

**Database** (`app/utils/db.py`): PostgreSQL connection pooling with psycopg2. Schema migrations in `sql/` directory.

**Auth & JWT** (`app/utils/auth.py`): JWT token generation/validation with Flask-JWT-Extended. Passwords hashed with bcrypt.

### Frontend Architecture

**Router**: React Router v6 with `App.tsx` as root. Routes: `/`, `/backtest`, `/watchlist`, `/login`, `/data-sources`.

**State Management**:
- Zustand store (`stores/useWatchlistStore.ts`) for watchlist state
- React Context (`contexts/AuthContext.tsx`) for authentication
- Local component state for backtest UI

**API Client** (`services/api.ts`): Centralized axios instance with request/response interceptors. Auto-adds JWT token, handles 401 redirects. Modules: `stockApi`, `strategyApi`, `backtestApi`, `watchlistApi`, `adapterApi`.

**Charts**: ECharts via `echarts-for-react`. `KLineChart.tsx` renders candlesticks with buy/sell markers. `EquityCurveChart.tsx` shows equity curve with benchmark comparison.

**Key Pages**:
- `BacktestPage.tsx`: Main backtesting interface (40KB+, largest component)
- `WatchlistPage.tsx`: Stock watchlist with group filtering
- `DataSourcePage.tsx`: Adapter health monitoring and metrics

### Database Schema

**Users** (`users` table): `id`, `username`, `password_hash`, `email`, `created_at`

**Watchlist Groups** (`watchlist_groups`): `id`, `user_id`, `name`, `description`, `is_default`, `created_at`

**Watchlist Items** (`watchlist_items`): `id`, `user_id`, `group_id`, `stock_code`, `stock_name`, `notes`, `created_at`

## Build, Test, and Development Commands

### Backend Development
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py  # Starts Flask dev server on port 4001
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev  # Starts Vite dev server on port 4000
npm run build  # TypeScript compilation + production build
npm run lint  # ESLint checking
npm run preview  # Preview production build
```

### Docker Operations (Preferred for deployment)
```bash
make up           # Start all services (postgres, backend, frontend)
make logs         # View all service logs
make logs-backend / make logs-frontend  # Service-specific logs
make down         # Stop all services
make restart      # Restart all services
make restart-backend / make restart-frontend  # Restart single service
make rebuild      # Full rebuild (no cache) and restart - AVOID unless necessary
make ps           # Show service status
make shell-backend / make shell-frontend  # Open shell in container
```

### Testing & Code Quality
```bash
pytest  # Run all tests (backend)
pytest tests/backtest/  # Run specific test suite
pytest -v tests/services/test_data_service.py  # Single test file
pytest -k test_ma_cross  # Run tests matching pattern
make test-backend  # Run pytest in Docker container

black app/  # Format backend code (88 char line length)
flake8 app/  # Lint backend code
make format-backend / make lint-backend  # Run in Docker
```

### Database Management
```bash
make reset-db  # Reset PostgreSQL database (WARNING: deletes all data)
# Database runs on localhost:5432 (postgres/stockpal user, stockpal_dev_2024 password)
```

### Adapter Health Checks
```bash
curl http://localhost:4001/api/v1/adapters/health  # Check all data sources
curl http://localhost:4001/api/v1/adapters/status  # Get adapter metadata + metrics
```

## Coding Style & Naming Conventions
Python code uses 4-space indents, type hints, and concise docstrings; keep files and functions in `snake_case`, classes in `PascalCase`, and reuse shared schemas before inventing new ones. Always run Black before committing and leave Flake8 clean. Frontend files use two-space indents, functional components in `PascalCase`, hooks/utilities in `camelCase`, and shared contracts exported from `src/types`.

## Testing Guidelines

Pytest is the authoritative framework. Mirror the module layout when adding tests (`backend/tests/test_data_service.py`, etc.), name cases `test_<behavior>`, and stub AkShare responses with fixtures or CSVs in `data/`. Use `pytest -q app/services` for quick feedback and `make test-backend` before pushing Docker changes. Frontend currently lacks suites, so new hooks or visualizations should ship with React Testing Library coverage.

**Test Organization**:
- `backend/tests/backtest/`: Backtest engine tests (orchestrator, trading engine, matching engine, metrics, validators, calendar, symbol classifier)
- `backend/tests/services/`: Service layer tests (watchlist, auth)
- `backend/tests/adapters/`: Data adapter tests (baostock)
- `backend/tests/conftest.py`: Shared fixtures (not present; use `backend/tests/backtest/conftest.py` for backtest fixtures)

**Test Data Strategy**:
- Mock external API calls (AkShare, yFinance, BaoStock) using pytest fixtures
- Store sample CSV datasets in `data/` directory for reproducible tests
- Use `backend/debug_scripts/` for manual testing/debugging scripts (not part of automated test suite)

**Running Specific Tests**:
```bash
pytest tests/backtest/test_orchestrator.py  # Single test file
pytest tests/backtest/test_orchestrator.py::TestBacktestOrchestrator::test_basic_backtest  # Single test
pytest -v tests/services/  # Verbose output for a directory
pytest -k "test_ma"  # Run tests matching pattern
```

## Commit & Pull Request Guidelines
Existing commits are short, imperative subjects (“add”, “init the project”); keep that tone or use concise Conventional Commit prefixes. Every PR should summarize scope, link issues, list the commands you ran (`pytest`, `npm run lint`, `make up`), and attach screenshots for UI updates. Favor small, topical commits to speed up review.

## Security & Configuration Tips

Copy `.env.example` or `.env.docker` before local runs, and never commit populated env files or AkShare credentials. Add new configuration keys through `app/config.py` and mirror them in `frontend/.env.development` only if the browser needs them. Keep cached data or logs inside `data/` and keep Docker volumes read-only.

**Environment Variables** (set in `docker-compose.yml` or `.env`):
- `DATA_SOURCE`: Primary data adapter (`akshare`, `yfinance`, `baostock`) - defaults to `akshare`
- `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`: Database credentials
- `JWT_SECRET_KEY`: Must be set in production for secure token signing
- `FLASK_ENV`: `development` or `production`
- `CORS_ORIGINS`: Comma-separated allowed origins for CORS

**Config Classes** (`backend/app/config.py`):
- `DevelopmentConfig`: Debug enabled, relaxed CORS
- `ProductionConfig`: Debug disabled, Gunicorn, restricted CORS
- `TestConfig`: Isolated test database settings

**Secrets Management**:
- Store JWT secret in environment variable, not code
- Database password in docker-compose.yml (development) or Kubernetes secrets (production)
- Never commit `.env` files with real credentials

**Port Assignments** (see `PORT_INFO.md` for full list):
- Backend API: 4001 (internal 5000)
- Frontend dev: 4000 + 4080 (dual exposure)
- PostgreSQL: 5432
