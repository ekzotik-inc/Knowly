from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_twa_init_data
from app.auth.session import create_access_token
from app.auth.telegram import TelegramAuthError, validate_init_data
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.repositories.users import UserRepository

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: str


@router.post("/telegram", response_model=AuthResponse)
async def authenticate_telegram(
    raw_init_data: str = Depends(get_twa_init_data),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    try:
        validated = validate_init_data(
            raw_init_data,
            settings.telegram_bot_token,
            max_age_seconds=settings.auth_data_max_age_seconds,
        )
    except (TelegramAuthError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication",
        ) from exc

    data = validated.user
    user = await UserRepository(db).get_or_create_from_telegram(
        telegram_id=data["id"],
        first_name=str(data.get("first_name", "Telegram user"))[:128],
        last_name=str(data["last_name"])[:128] if data.get("last_name") else None,
        username=str(data["username"])[:64] if data.get("username") else None,
        language_code=str(data["language_code"])[:16] if data.get("language_code") else None,
    )
    await db.commit()

    ttl_seconds = settings.session_ttl_days * 24 * 60 * 60
    return AuthResponse(
        access_token=create_access_token(user.id, settings.session_secret, ttl_seconds),
        expires_in=ttl_seconds,
        user_id=str(user.id),
    )
