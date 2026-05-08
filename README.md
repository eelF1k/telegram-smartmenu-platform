# SmartMenu Platform

SmartMenu is a multi-module Telegram-first platform for restaurant digital menus, ordering, table reservations, loyalty, and analytics.

## Phase 0 (Bootstrap)

- Monorepo structure initialized (`bot`, `api`, `webapp`, `infra`, `tests`, `shared`)
- Base Python stack configured (aiogram, FastAPI, SQLAlchemy, Redis)
- Docker Compose for local infrastructure and services
- CI workflow for lint + tests
- Starter API and bot placeholders

## Phase 1 (Bot Core)

- aiogram 3.x dispatcher factory with routers and middlewares
- Commands: `/start`, `/menu`, `/profile`, `/reserve`, `/support`, `/referral`, `/help`, `/cancel`
- FSM skeleton for reservation flow
- Webhook endpoint in API with `WEBHOOK_SECRET` validation
- Runtime switch via `BOT_MODE=polling|webhook`

## Phase 2 (Ordering FSM + Pagination)

- `/menu` now starts a real FSM ordering flow
- Inline callbacks for venue/category/dish/modifier/payment
- Pagination for categories and dishes via callback buttons
- Multi-step order state: venue -> category -> dish -> modifiers -> destination -> payment
- Reservation flow isolated into separate FSM states

## Phase 3 (Telegram WebApp Foundation)

- React + TypeScript + Vite client in `webapp/`
- Telegram WebApp SDK integration (`ready`, `expand`, `MainButton`, `BackButton`, `sendData`)
- Screens: Menu, Cart, Profile (React Router)
- Cart persistence in localStorage
- API integration: `/webapp/menu`, `/webapp/profile/{user_id}`, `/webapp/confirm`

## Phase 4 (DB + UoW Foundation)

- SQLAlchemy 2.0 async models: `users`, `venues`, `categories`, `dishes`, `orders`
- Alembic scaffold with initial migration (`0001_initial_schema`)
- Async session factory and Unit of Work abstraction
- Repository layer (`UserRepository`, `VenueRepository`)
- `/webapp/profile/{user_id}` now uses repository/UoW (with local fallback when DB is offline)

## Phase 5 (Payments + Referrals)

- Deep-link referrals: `/start ref123` payload parsing and registration
- Referral dashboard in `/referral` (invite count)
- Payment catalog via `/pricing`
- Invoice issuing via `/buy <product_id>`
- Payment hooks: `pre_checkout_query` + `successful_payment`

## Phase 6 (Admin Tooling + Reservations Dashboard)

- Admin commands in bot: `/admin`, `/bookings_admin`, `/orders_admin`
- Reservation records now stored and status-managed in shared admin store
- Admin API endpoints:
  - `GET /admin/reservations`
  - `POST /admin/reservations/{id}/status`
  - `GET /admin/orders`
  - `POST /admin/orders/{id}/status`
- WebApp Admin screen with reservation/order status actions

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
copy .env.example .env
pip install -e ".[dev]"
docker compose up -d postgres redis
python -m uvicorn api.app:app --reload --port 8000
python -m bot.main
cd webapp && npm install && npm run dev
```

### Database Bootstrap

```bash
docker compose up -d postgres redis
alembic upgrade head
```

### Bot Runtime Modes

- `BOT_MODE=polling` -> `python -m bot.main` starts polling.
- `BOT_MODE=webhook` -> updates are handled by `POST /telegram/webhook/{WEBHOOK_SECRET}` in API.

## Next Steps

- Phase 7: AI recommendations + SSE response stream
