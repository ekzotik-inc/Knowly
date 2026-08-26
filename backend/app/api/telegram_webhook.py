from __future__ import annotations

from hmac import compare_digest

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import ValidationError

from app.core.config import settings
from bot.main import bot, dp

router = APIRouter(tags=["telegram"])


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    expected = settings.webhook_secret
    if not expected or not x_telegram_bot_api_secret_token or not compare_digest(
        x_telegram_bot_api_secret_token,
        expected,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram webhook secret",
        )

    try:
        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": bot})
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram update",
        ) from exc

    await dp.feed_update(bot, update)
    return {"ok": True}
