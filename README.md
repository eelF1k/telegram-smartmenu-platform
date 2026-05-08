# SmartMenu Platform

`SmartMenu Platform` — це Telegram-first платформа цифрового меню для закладів, яка об'єднує:
- клієнтський Telegram-бот на `aiogram 3.x`;
- WebApp на `React + TypeScript`;
- бекенд на `FastAPI`;
- модулі оплати, рекомендацій, нотифікацій, політик доставки та спостережуваності.

Проєкт оформлений як публічний портфоліо-showcase рівня middle+/senior: з архітектурним поділом, тестами, CI-підходом і продакшн-патернами.

## Що демонструє цей проєкт

- Розробку складних Telegram-ботів (FSM, callback-flow, payment flow, webhook security).
- Інтеграцію Telegram WebApp, API-шару та адмін-інструментів в єдину систему.
- Асинхронну архітектуру: черги, retry/backoff, dead-letter, outbox, delivery adapters.
- Спостережуваність: метрики, trace-id, OTEL wiring.
- Продуктовий підхід: policy engine, tenant-aware routing, runtime policy management.

## Ключовий функціонал

### Telegram Bot
- Команди `/start`, `/menu`, `/profile`, `/reserve`, `/support`, `/referral`, `/pricing`, `/buy`.
- FSM-замовлення: заклад -> категорія -> страва -> модифікатори -> локація -> оплата.
- Бронювання, реферальні deep links, sandbox payment flow.
- i18n (`uk`, `en`) через middleware.

### WebApp + API
- Екрани меню, кошика, профілю, admin, AI-рекомендацій.
- API для меню, профілю, підтвердження замовлень, адмін-функцій і policy management.
- SSE endpoint для потокових AI-відповідей.

### Queue + Delivery Pipeline
- In-memory/Redis queue backend, worker loop, retry/backoff, dead-letter.
- Delivery adapters: `telegram`, `webhook`, `email (SMTP)`.
- Persistent DB outbox + idempotent доставка.

### Policy Engine
- Routing policy за `channel` і `priority`.
- Rate caps.
- Tenant-aware limits.
- Venue overrides.
- Runtime керування правилами через admin API.
- Dry-run simulation endpoint для перевірки policy decisions.

### Observability
- Prometheus метрики (`/metrics`).
- Queue/delivery counters + histograms.
- Trace-id у critical path.
- OpenTelemetry bootstrap wiring для OTLP exporter.

## Технології

- **Backend:** `Python`, `FastAPI`, `aiogram 3.x`, `SQLAlchemy 2.0`, `Alembic`
- **Async/Queue:** `asyncio`, in-memory queue, Redis queue backend, ARQ-ready wiring
- **DB/Storage:** `PostgreSQL`, `Redis`
- **Frontend:** `React`, `TypeScript`, `Vite`, Telegram WebApp SDK
- **Payments/Delivery:** Telegram Payments, SMTP (`aiosmtplib`), HTTP/webhook adapters
- **Observability:** `prometheus-client`, OpenTelemetry (`opentelemetry-*`)
- **Testing/Quality:** `pytest`, `httpx`, `ruff`

## Архітектура

```text
telegram-smartmenu-platform/
├── api/        # FastAPI endpoints, worker entrypoints, DB models/migrations
├── bot/        # aiogram app, FSM, middlewares, handlers
├── shared/     # queue, policy, outbox, adapters, observability
├── webapp/     # React + TypeScript Telegram WebApp
├── tests/      # unit + integration tests
└── infra/      # docker artifacts
```

## Швидкий старт

```bash
copy .env.example .env
pip install -e ".[dev]"
docker compose up -d postgres redis
alembic upgrade head
python -m uvicorn api.app:app --reload --port 8000
python -m bot.main
cd webapp && npm install && npm run dev
```

## Основні змінні оточення

- `BOT_MODE`, `WEBHOOK_SECRET`
- `DATABASE_URL`, `REDIS_URL`
- `QUEUE_BACKEND`, `QUEUE_REDIS_PREFIX`
- `DELIVERY_WEBHOOK_URL`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`
- `OTEL_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`
- `DELIVERY_RATE_LIMIT_PER_MINUTE`

## Якість і перевірки

```bash
python -m ruff check .
python -m pytest -q
```

CI налаштований так, щоб кожен коміт проходив форматування, lint і тести.

## Поточний статус roadmap

Реалізовано кроки `0 -> 19`:
- бот + FSM + WebApp foundation;
- DB/UoW + migrations;
- payments + referrals;
- admin dashboard endpoints;
- AI recommendations + SSE;
- queue worker pipeline (retry/backoff/dead-letter);
- adapters + outbox + persistent policy rules;
- tenant-aware policy + dry-run simulation + observability.

## Про автора

Цей репозиторій представляє практичний стиль роботи розробника з комерційним досвідом у Telegram-автоматизації:
- **25+ реалізованих ботів різної складності**;
- досвід побудови production-сценаріїв із асинхронною обробкою, платежами, FSM, інтеграціями та аналітикою;
- значна частина реальних робіт під NDA, тому цей репозиторій використовується як публічний технічний showcase.
