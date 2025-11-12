# Repository Guidelines

所有端口相关配置都要先参考 PORT_INFO.md，确保与现有服务不冲突。
目前项目处于早期阶段，所有的详细设计和开发计划都不需要考虑数据迁移之类的内容。

## Project Structure & Module Organization
`backend/app` hosts the Flask stack: `api/v1` exposes REST resources, `services` implements data, indicator, strategy, and backtest logic, and `utils`/`models` provide shared helpers beside the `run.py` entrypoint. React code stays in `frontend/src` (`pages`, `components`, `services/api.ts`, `types`). Root automation relies on `Makefile` plus `docker-compose.yml`; supporting docs live in `doc/` and cacheable datasets belong in `data/`.

## Build, Test, and Development Commands
- `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` – bootstrap backend dependencies.
- `python run.py` – launch the API at `http://localhost:4001`.
- `pytest` or `make test-backend` – run backend suites locally or inside Docker.
- `black app/ && flake8 app/` – enforce Python formatting and linting.
- `cd frontend && npm install && npm run dev` – install dependencies and start the Vite dev server on port 4000 (`npm run build` / `npm run lint` for prod builds and ESLint).
- `make up`, `make logs`, `make down` – build, inspect, and stop the full compose stack.

## Coding Style & Naming Conventions
Python code uses 4-space indents, type hints, and concise docstrings; keep files and functions in `snake_case`, classes in `PascalCase`, and reuse shared schemas before inventing new ones. Always run Black before committing and leave Flake8 clean. Frontend files use two-space indents, functional components in `PascalCase`, hooks/utilities in `camelCase`, and shared contracts exported from `src/types`.

## Testing Guidelines
Pytest is the authoritative framework. Mirror the module layout when adding tests (`backend/tests/test_data_service.py`, etc.), name cases `test_<behavior>`, and stub AkShare responses with fixtures or CSVs in `data/`. Use `pytest -q app/services` for quick feedback and `make test-backend` before pushing Docker changes. Frontend currently lacks suites, so new hooks or visualizations should ship with React Testing Library coverage.

## Commit & Pull Request Guidelines
Existing commits are short, imperative subjects (“add”, “init the project”); keep that tone or use concise Conventional Commit prefixes. Every PR should summarize scope, link issues, list the commands you ran (`pytest`, `npm run lint`, `make up`), and attach screenshots for UI updates. Favor small, topical commits to speed up review.

## Security & Configuration Tips
Copy `.env.example` or `.env.docker` before local runs, and never commit populated env files or AkShare credentials. Add new configuration keys through `app/config.py` and mirror them in `frontend/.env.development` only if the browser needs them. Keep cached data or logs inside `data/` and keep Docker volumes read-only.
