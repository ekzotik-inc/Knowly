from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.db.models import Achievement, UserAchievement, UserProgress
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/progression", tags=["progression"])


class ProgressResponse(BaseModel):
    xp: int
    level: int
    next_level_xp: int
    tests_created: int
    tests_completed: int


class AchievementResponse(BaseModel):
    code: str
    title: str
    description: str
    icon: str
    unlocked: bool


@router.get("", response_model=ProgressResponse)
async def get_progress(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProgressResponse:
    progress = await db.scalar(select(UserProgress).where(UserProgress.user_id == current_user.id))
    if progress is None:
        progress = UserProgress(user_id=current_user.id)
        db.add(progress)
        await db.commit()
    return ProgressResponse(
        xp=progress.xp,
        level=progress.level,
        next_level_xp=progress.level * 100,
        tests_created=progress.tests_created,
        tests_completed=progress.tests_completed,
    )


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[AchievementResponse]:
    achievements = list((await db.execute(select(Achievement).order_by(Achievement.code))).scalars())
    unlocked = set((await db.execute(select(UserAchievement.achievement_id).where(UserAchievement.user_id == current_user.id))).scalars())
    return [
        AchievementResponse(
            code=item.code,
            title=item.title,
            description=item.description,
            icon=item.icon,
            unlocked=item.id in unlocked,
        )
        for item in achievements
    ]
