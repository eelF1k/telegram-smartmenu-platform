# SmartMenu Platform

SmartMenu is a multi-module Telegram-first platform for restaurant digital menus, ordering, table reservations, loyalty, and analytics.

## Phase 0 (Bootstrap)

- Monorepo structure initialized (`bot`, `api`, `webapp`, `infra`, `tests`, `shared`)
- Base Python stack configured (aiogram, FastAPI, SQLAlchemy, Redis)
- Docker Compose for local infrastructure and services
- CI workflow for lint + tests
- Starter API and bot placeholders

## Repository Structure

```text
telegram-smartmenu-platform/
├── api/
├── bot/
├── infra/
│   └── docker/
├── shared/
├── tests/
└── webapp/
```

## Quick Start

```bash
pip install -e ".[dev]"
docker compose up -d postgres redis
python -m uvicorn api.app:app --reload --port 8000
```

## Next Steps

- Phase 1: aiogram 3 bot core, routers, FSM, middleware
- Phase 2: menu ordering flow and Redis FSM storage
- Phase 3: Telegram WebApp (React + TWA SDK)
- Phase 4: database layer, repositories, migrations
