from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.db.models import Profile
from app.db.session import get_db
from app.services.character import CharacterConfig, DEFAULT_CHARACTER

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


class ProfilePayload(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    avatar_url: str | None = Field(default=None, max_length=512)
    character: CharacterConfig | None = None


class ProfileResponse(ProfilePayload):
    id: uuid.UUID
    character: CharacterConfig


async def _get_or_create_profile(db: AsyncSession, user_id: uuid.UUID, default_name: str) -> Profile:
    profile = await db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is None:
        profile = Profile(
            user_id=user_id,
            display_name=default_name,
            character_config=DEFAULT_CHARACTER.model_dump(),
        )
        db.add(profile)
        await db.flush()
    elif not profile.character_config:
        profile.character_config = DEFAULT_CHARACTER.model_dump()
    return profile


def _response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        character=CharacterConfig.model_validate(profile.character_config or {}),
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    profile = await _get_or_create_profile(db, current_user.id, current_user.first_name)
    await db.commit()
    return _response(profile)


@router.put("", response_model=ProfileResponse)
async def update_profile(
    payload: ProfilePayload,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    profile = await _get_or_create_profile(db, current_user.id, current_user.first_name)
    profile.display_name = payload.display_name.strip()
    profile.avatar_url = payload.avatar_url
    if payload.character is not None:
        profile.character_config = payload.character.model_dump()
    await db.commit()
    return _response(profile)
