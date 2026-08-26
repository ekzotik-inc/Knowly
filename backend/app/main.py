from contextlib import asynccontextmanager

from aiogram.types import BotCommand
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.tests import router as tests_router
from app.api.payments import router as payments_router
from app.api.profile import router as profile_router
from app.api.progression import router as progression_router
from app.api.telegram_webhook import router as telegram_webhook_router
from app.core.config import settings
from app.db.bootstrap import initialize_database
from bot.main import bot


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    if settings.environment == "production" and settings.telegram_webhook_url and settings.webhook_secret:
        await bot.set_my_commands([
            BotCommand(command="start", description="Открыть Knowly"),
            BotCommand(command="help", description="Как играть"),
            BotCommand(command="terms", description="Конфиденциальность"),
            BotCommand(command="paysupport", description="Поддержка оплаты"),
        ])
        await bot.set_webhook(
            url=settings.telegram_webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=["message", "pre_checkout_query"],
            drop_pending_updates=False,
        )
    yield
    await bot.session.close()


app = FastAPI(title="Knowly API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Telegram-Bot-Api-Secret-Token"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(payments_router)
app.include_router(profile_router)
app.include_router(progression_router)
app.include_router(tests_router)
app.include_router(telegram_webhook_router)
