from typing import Literal
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.db.models import Profile
from app.db.session import get_db
from app.services.character import CharacterConfig, DEFAULT_CHARACTER, MASCULINE_CHARACTER

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


class CharacterPair(BaseModel):
    feminine: CharacterConfig = Field(default_factory=lambda: DEFAULT_CHARACTER.model_copy(deep=True))
    masculine: CharacterConfig = Field(default_factory=lambda: MASCULINE_CHARACTER.model_copy(deep=True))


class ProfilePayload(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    avatar_url: str | None = Field(default=None, max_length=512)
    character: CharacterConfig | None = None
    characters: CharacterPair | None = None
    locale: Literal["ru", "en", "uz"] = "ru"
    result_visibility: Literal["name", "anonymous", "name_avatar"] = "name"
    sound_enabled: bool = True
    haptic_enabled: bool = True


class ProfileResponse(ProfilePayload):
    id: uuid.UUID
    character: CharacterConfig
    characters: CharacterPair


def _pair_from_config(raw: dict | None) -> CharacterPair:
    if raw and "feminine" in raw and "masculine" in raw:
        return CharacterPair.model_validate(raw)
    legacy = CharacterConfig.model_validate(raw or {})
    if legacy.gender == "masculine":
        return CharacterPair(feminine=DEFAULT_CHARACTER, masculine=legacy)
    return CharacterPair(feminine=legacy, masculine=MASCULINE_CHARACTER)


async def _get_or_create_profile(db: AsyncSession, user_id: uuid.UUID, default_name: str) -> Profile:
    profile = await db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is None:
        profile = Profile(
            user_id=user_id,
            display_name=default_name,
            character_config=CharacterPair().model_dump(),
        )
        db.add(profile)
        await db.flush()
    else:
        profile.character_config = _pair_from_config(profile.character_config).model_dump()
    return profile


def _response(profile: Profile) -> ProfileResponse:
    pair = _pair_from_config(profile.character_config)
    return ProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        character=pair.feminine,
        characters=pair,
        locale=profile.locale,
        result_visibility=profile.result_visibility,
        sound_enabled=profile.sound_enabled,
        haptic_enabled=profile.haptic_enabled,
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
    if payload.characters is not None:
        profile.character_config = payload.characters.model_dump()
    elif payload.character is not None:
        profile.character_config = _pair_from_config(payload.character.model_dump()).model_dump()
    profile.locale = payload.locale
    profile.result_visibility = payload.result_visibility
    profile.sound_enabled = payload.sound_enabled
    profile.haptic_enabled = payload.haptic_enabled
    await db.commit()
    return _response(profile)
