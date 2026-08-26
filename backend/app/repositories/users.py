from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_from_telegram(
        self,
        *,
        telegram_id: int,
        first_name: str,
        last_name: str | None,
        username: str | None,
        language_code: str | None,
    ) -> User:
        user = await self.db.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is None:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                language_code=language_code,
            )
            self.db.add(user)
            await self.db.flush()
            return user

        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.language_code = language_code
        await self.db.flush()
        return user
