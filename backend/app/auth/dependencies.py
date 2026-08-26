from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import verify_access_token
from app.auth.telegram import TelegramAuthError, validate_init_data
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.repositories.users import UserRepository


class TelegramUserPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


def get_twa_init_data(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    scheme, separator, credentials = authorization.partition(" ")
    if scheme != "TWA" or not separator or not credentials.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return credentials.strip()


def get_authorization(
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[str, str]:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    scheme, separator, credentials = authorization.partition(" ")
    if not separator or not credentials.strip() or scheme.lower() not in {"bearer", "twa"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return scheme.lower(), credentials.strip()


async def get_current_user(
    authorization: Annotated[tuple[str, str], Depends(get_authorization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    scheme, credentials = authorization
    if scheme == "bearer":
        user_id = verify_access_token(credentials, settings.session_secret)
        user = await db.get(User, user_id) if user_id else None
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
        return user

    try:
        validated = validate_init_data(
            credentials,
            settings.telegram_bot_token,
            max_age_seconds=settings.auth_data_max_age_seconds,
        )
        telegram_user = TelegramUserPayload.model_validate(validated.user)
    except (TelegramAuthError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram authentication")

    user = await UserRepository(db).get_or_create_from_telegram(
        telegram_id=telegram_user.id,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
        username=telegram_user.username,
        language_code=telegram_user.language_code,
    )
    await db.commit()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
