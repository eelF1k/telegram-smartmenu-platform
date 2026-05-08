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

## Phase 7 (AI Recommendations + SSE)

- Lightweight recommendation engine in `api/recommendations.py`
- Endpoint `GET /webapp/recommendations/{user_id}?q=...` for ranked dish suggestions
- SSE endpoint `GET /webapp/recommendations-stream?user_id=...&q=...` for streamed AI-style output
- WebApp `AI` screen with query input, recommendation list, and live SSE log
- API tests extended for recommendation and streaming endpoints

## Phase 8 (i18n ua/en + Localization Middleware)

- Added `bot/i18n.py` with translation catalog (`uk`, `en`) and locale detection
- Added `LocalizationMiddleware` to inject `locale` and `t()` translator into handlers
- Localized key command responses (`/start`, `/help`, `/menu`, `/profile`, `/reserve`, `/support`, `/referral`, `/cancel`)
- Localized middleware replies for throttling and banned users
- Added tests for locale detection and message translation

## Phase 9 (Queue Worker + Async Notification Jobs)

- Added in-memory queue layer `shared/queue_jobs.py` with job lifecycle (`pending`, `processing`, `done`, `failed`)
- Added queue API endpoints:
  - `POST /queue/enqueue`
  - `GET /queue/jobs?status=...`
  - `POST /queue/process-next`
- Added automatic enqueueing for notification jobs when:
  - order is created via `/webapp/confirm`
  - reservation status changes in admin API
  - order status changes in admin API
- Added worker runner `api/worker.py` for continuous background processing
- Added integration tests for queue endpoints and status-change enqueue behavior

## Phase 10 (Retry/Backoff + Dead-Letter + Queue Adapter)

- Extended queue model with retry metadata: `max_attempts`, `backoff_seconds`, `available_at`
- Added exponential backoff scheduling on failures
- Added dead-letter behavior (`dead_letter` status) after retry limit is reached
- Added queue adapter abstraction in `shared/queue_adapter.py`:
  - `InMemoryQueueAdapter` (active)
  - `ArqQueueAdapter` (stub for next infra step)
  - `CeleryQueueAdapter` (stub for next infra step)
- Unified processing logic in `shared/queue_processor.py` and reused by API/worker
- Added API support for custom retry settings in `POST /queue/enqueue`
- Added tests for retry -> dead-letter flow

## Phase 11 (Redis Queue Backend + ARQ Wiring)

- Added queue backend factory `shared/queue_factory.py` with runtime backend selection
- Added Redis-backed queue store `shared/redis_queue.py` (same lifecycle as memory queue)
- Switched API/worker to use `queue_store` abstraction instead of hardcoded in-memory queue
- Added optional ARQ worker wiring in `api/arq_worker.py` (ready to run after installing `arq`)
- Added queue backend tests and config updates:
  - `QUEUE_BACKEND=memory|redis`
  - `QUEUE_REDIS_PREFIX=smartmenu:queue`

## Phase 12 (Delivery Adapters + Idempotent Notification Outbox)

- Added delivery adapter registry `shared/delivery_adapters.py`:
  - Telegram adapter
  - Email adapter
  - Webhook adapter
- Added idempotent notification outbox `shared/notification_outbox.py` with dedupe keys
- Extended queue processing to:
  - route supported notification jobs by channel
  - avoid duplicate delivery by checking outbox dedupe key
  - persist delivery records in outbox
- Integrated outbox + adapters in API processing endpoint and background worker
- Added `GET /queue/outbox` endpoint for monitoring delivered notification records
- Added tests for adapter registry and idempotent duplicate processing

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

- Phase 13: persistent DB outbox + real transport integrations (SMTP/HTTP/Telegram API)
