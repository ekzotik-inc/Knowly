from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProgress


XP_PER_LEVEL = 100


def level_for_xp(xp: int) -> int:
    return max(1, xp // XP_PER_LEVEL + 1)


async def award_xp(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    amount: int,
    created_test: bool = False,
    completed_test: bool = False,
) -> UserProgress:
    if amount <= 0:
        raise ValueError("XP amount must be positive")
    progress = await db.scalar(select(UserProgress).where(UserProgress.user_id == user_id).with_for_update())
    if progress is None:
        progress = UserProgress(user_id=user_id)
        db.add(progress)
        await db.flush()
    progress.xp += amount
    progress.level = level_for_xp(progress.xp)
    if created_test:
        progress.tests_created += 1
    if completed_test:
        progress.tests_completed += 1
    return progress
