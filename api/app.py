import asyncio

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select

from api.db import SessionFactory
from api.models import DeliveryPolicyRule
from api.recommendations import build_recommendation_text, recommend_dishes
from api.uow import uow_context
from bot.app import create_bot, create_dispatcher
from bot.config import BotSettings
from bot.menu_data import MENU_DATA
from shared.admin_store import admin_store
from shared.delivery_adapters import build_delivery_adapters
from shared.delivery_policy import DeliveryPolicyEngine
from shared.observability import export_metrics, new_trace_id
from shared.outbox_store import outbox_store
from shared.queue_factory import build_queue_store
from shared.queue_processor import process_next_job
from shared.tracing import setup_tracing

app = FastAPI(title="SmartMenu API", version="0.1.0")
settings = BotSettings()
setup_tracing("smartmenu-api")
bot = create_bot(settings)
dispatcher = create_dispatcher(settings)
queue_store = build_queue_store(
    settings.queue_backend,
    redis_url=settings.redis_url,
    redis_prefix=settings.queue_redis_prefix,
)
delivery_adapters = build_delivery_adapters()
policy_engine = DeliveryPolicyEngine(rate_limit_per_minute=settings.delivery_rate_limit_per_minute)
policy_rules_fallback: list[dict] = []


async def reload_policy_rules() -> None:
    policy_engine.clear_rules()
    try:
        async with SessionFactory() as session:
            result = await session.execute(select(DeliveryPolicyRule))
            rows = result.scalars().all()
            for row in rows:
                if row.scope == "tenant" and row.rate_limit_per_minute:
                    policy_engine.set_tenant_rate_limit(
                        tenant_id=row.scope_key,
                        limit_per_minute=row.rate_limit_per_minute,
                    )
                if row.scope == "venue":
                    policy_engine.set_venue_override(
                        row.scope_key,
                        channel=row.channel,
                        priority=row.priority,
                    )
            return
    except Exception:
        pass

    for row in policy_rules_fallback:
        if row["scope"] == "tenant" and row.get("rate_limit_per_minute"):
            policy_engine.set_tenant_rate_limit(
                tenant_id=row["scope_key"],
                limit_per_minute=int(row["rate_limit_per_minute"]),
            )
        if row["scope"] == "venue":
            policy_engine.set_venue_override(
                row["scope_key"],
                channel=row.get("channel"),
                priority=row.get("priority"),
            )


@app.on_event("startup")
async def startup_policy_reload() -> None:
    try:
        await reload_policy_rules()
    except Exception:
        # Keep API bootable when DB is unavailable in demo mode.
        pass


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    payload, content_type = export_metrics()
    return Response(content=payload, media_type=content_type)


@app.get("/webapp/menu")
async def webapp_menu() -> dict:
    return {"ok": True, "venues": MENU_DATA}


@app.get("/webapp/profile/{user_id}")
async def webapp_profile(user_id: int) -> dict:
    user_payload = {
        "user_id": user_id,
        "username": f"user{user_id}",
        "locale": settings.default_locale,
    }
    try:
        async with uow_context() as uow:
            user = await uow.users.get_by_telegram_id(user_id)
            if not user:
                user = await uow.users.create_user(
                    telegram_id=user_id,
                    username=f"user{user_id}",
                    locale=settings.default_locale,
                )
            user_payload = {
                "user_id": user.telegram_id,
                "username": user.username,
                "locale": user.locale,
            }
    except Exception:
        # If DB is not available, keep endpoint usable in local demo mode.
        pass

    return {
        "ok": True,
        "profile": {
            "user_id": user_payload["user_id"],
            "username": user_payload["username"],
            "locale": user_payload["locale"],
            "loyalty_points": 120,
            "orders_count": 7,
            "preferred_venue": "vinson-git",
        },
    }


@app.post("/webapp/confirm")
async def webapp_confirm(payload: dict) -> dict:
    user_id = int(payload.get("user_id", 0))
    total = int(payload.get("total", 0))
    order = admin_store.create_order(user_id=user_id, total=total)
    queue_store.enqueue(
        kind="notify_order_created",
        payload={"user_id": user_id, "order_id": order.order_id, "total": total},
    )
    return {"ok": True, "received": payload}


@app.get("/webapp/recommendations-stream")
async def webapp_recommendations_stream(user_id: int, q: str = "") -> StreamingResponse:
    async def event_stream():
        text = build_recommendation_text(user_query=q or "щось смачне")
        for chunk in text.split("\n"):
            await asyncio.sleep(0.05)
            yield f"data: {chunk}\n\n"
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/webapp/recommendations/{user_id}")
async def webapp_recommendations(user_id: int, q: str = "") -> dict:
    # user_id reserved for future personalized ranking by order history
    _ = user_id
    items = recommend_dishes(user_query=q or "популярне", limit=5)
    return {
        "ok": True,
        "items": [
            {
                "venue_id": item.venue_id,
                "venue_name": item.venue_name,
                "category_id": item.category_id,
                "category_name": item.category_name,
                "dish_id": item.dish_id,
                "dish_name": item.dish_name,
                "price": item.price,
                "score": item.score,
            }
            for item in items
        ],
    }


@app.get("/admin/reservations")
async def admin_reservations() -> dict:
    return {"ok": True, "reservations": [r.__dict__ for r in admin_store.list_reservations()]}


@app.post("/admin/reservations/{reservation_id}/status")
async def admin_update_reservation_status(reservation_id: int, payload: dict) -> dict:
    status = str(payload.get("status", "")).strip()
    if status not in {"pending", "accepted", "rejected", "cancelled"}:
        raise HTTPException(status_code=400, detail="invalid_reservation_status")
    updated = admin_store.update_reservation_status(reservation_id=reservation_id, status=status)
    if not updated:
        raise HTTPException(status_code=404, detail="reservation_not_found")
    queue_store.enqueue(
        kind="notify_reservation_status",
        payload={
            "user_id": updated.user_id,
            "reservation_id": updated.reservation_id,
            "status": updated.status,
        },
    )
    return {"ok": True, "reservation": updated.__dict__}


@app.get("/admin/orders")
async def admin_orders() -> dict:
    return {"ok": True, "orders": [o.__dict__ for o in admin_store.list_orders()]}


@app.get("/admin/policy-rules")
async def admin_policy_rules() -> dict:
    try:
        async with SessionFactory() as session:
            result = await session.execute(select(DeliveryPolicyRule))
            rules = result.scalars().all()
        return {
            "ok": True,
            "rules": [
                {
                    "id": row.id,
                    "scope": row.scope,
                    "scope_key": row.scope_key,
                    "channel": row.channel,
                    "priority": row.priority,
                    "rate_limit_per_minute": row.rate_limit_per_minute,
                }
                for row in rules
            ],
        }
    except Exception:
        return {"ok": True, "rules": policy_rules_fallback}


@app.post("/admin/policy-rules")
async def admin_upsert_policy_rule(payload: dict) -> dict:
    scope = str(payload.get("scope", "")).strip()
    scope_key = str(payload.get("scope_key", "")).strip()
    if scope not in {"tenant", "venue"}:
        raise HTTPException(status_code=400, detail="invalid_scope")
    if not scope_key:
        raise HTTPException(status_code=400, detail="scope_key_required")
    try:
        async with SessionFactory() as session:
            result = await session.execute(
                select(DeliveryPolicyRule).where(
                    DeliveryPolicyRule.scope == scope,
                    DeliveryPolicyRule.scope_key == scope_key,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                row = DeliveryPolicyRule(scope=scope, scope_key=scope_key)
                session.add(row)
            row.channel = payload.get("channel")
            row.priority = payload.get("priority")
            row.rate_limit_per_minute = payload.get("rate_limit_per_minute")
            await session.commit()
    except Exception:
        updated = False
        for row in policy_rules_fallback:
            if row["scope"] == scope and row["scope_key"] == scope_key:
                row["channel"] = payload.get("channel")
                row["priority"] = payload.get("priority")
                row["rate_limit_per_minute"] = payload.get("rate_limit_per_minute")
                updated = True
                break
        if not updated:
            policy_rules_fallback.append(
                {
                    "scope": scope,
                    "scope_key": scope_key,
                    "channel": payload.get("channel"),
                    "priority": payload.get("priority"),
                    "rate_limit_per_minute": payload.get("rate_limit_per_minute"),
                }
            )
    await reload_policy_rules()
    return {"ok": True}


@app.post("/admin/orders/{order_id}/status")
async def admin_update_order_status(order_id: int, payload: dict) -> dict:
    status = str(payload.get("status", "")).strip()
    if status not in {"created", "accepted", "preparing", "delivering", "completed", "cancelled"}:
        raise HTTPException(status_code=400, detail="invalid_order_status")
    updated = admin_store.update_order_status(order_id=order_id, status=status)
    if not updated:
        raise HTTPException(status_code=404, detail="order_not_found")
    queue_store.enqueue(
        kind="notify_order_status",
        payload={
            "user_id": updated.user_id,
            "order_id": updated.order_id,
            "status": updated.status,
        },
    )
    return {"ok": True, "order": updated.__dict__}


@app.post("/queue/enqueue")
async def queue_enqueue(payload: dict) -> dict:
    kind = str(payload.get("kind", "")).strip()
    body = payload.get("payload", {})
    max_attempts = int(payload.get("max_attempts", 3))
    backoff_seconds = float(payload.get("backoff_seconds", 1.0))
    if not kind:
        raise HTTPException(status_code=400, detail="kind_required")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="payload_must_be_object")
    if max_attempts < 1:
        raise HTTPException(status_code=400, detail="max_attempts_must_be_positive")
    if backoff_seconds < 0:
        raise HTTPException(status_code=400, detail="backoff_seconds_must_be_non_negative")
    job = queue_store.enqueue(
        kind=kind,
        payload=body,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
    )
    return {"ok": True, "job": job.__dict__}


@app.get("/queue/jobs")
async def queue_jobs(status: str | None = None) -> dict:
    return {"ok": True, "jobs": [job.__dict__ for job in queue_store.list_jobs(status=status)]}


@app.post("/queue/process-next")
async def queue_process_next() -> dict:
    trace_id = new_trace_id()
    processed, job = await process_next_job(
        queue_store,
        outbox=outbox_store,
        delivery_adapters=delivery_adapters,
        policy_engine=policy_engine,
    )
    if not processed or not job:
        return {"ok": True, "processed": False, "trace_id": trace_id}
    status = next(item.status for item in queue_store.list_jobs() if item.job_id == job.job_id)
    return {
        "ok": True,
        "processed": True,
        "job_id": job.job_id,
        "status": status,
        "trace_id": trace_id,
    }


@app.get("/queue/outbox")
async def queue_outbox() -> dict:
    records = await outbox_store.list_records()
    return {
        "ok": True,
        "records": [record.__dict__ for record in records],
    }


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(
    secret: str,
    payload: dict,
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
) -> dict[str, bool]:
    if secret != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="invalid_webhook_secret")
    if (
        x_telegram_bot_api_secret_token
        and x_telegram_bot_api_secret_token != settings.webhook_secret
    ):
        raise HTTPException(status_code=401, detail="invalid_telegram_header_secret")

    update = Update.model_validate(payload)
    await dispatcher.feed_update(bot=bot, update=update)
    return {"ok": True}
