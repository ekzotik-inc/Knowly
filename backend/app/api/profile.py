from typing import Literal
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.db.models import Profile
from app.db.session import get_db
from app.services.character import CharacterConfig, DEFAULT_CHARACTER, MASCULINE_CHARACTER

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


class CharacterPair(BaseModel):
    """Legacy input shape accepted once so existing clients can migrate safely."""

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


class ProfileResponse(BaseModel):
    id: uuid.UUID
    display_name: str
    avatar_url: str | None
    character: CharacterConfig | None
    onboarding_required: bool
    locale: Literal["ru", "en", "uz"]
    result_visibility: Literal["name", "anonymous", "name_avatar"]
    sound_enabled: bool
    haptic_enabled: bool


def _single_from_config(raw: dict | None) -> CharacterConfig | None:
    """Return the user's character and migrate legacy pair config to its feminine side."""
    if not raw or raw.get("onboarding_required"):
        return None
    if "feminine" in raw and "masculine" in raw:
        try:
            return CharacterPair.model_validate(raw).feminine
        except ValidationError:
            return None
    try:
        return CharacterConfig.model_validate(raw)
    except ValidationError:
        return None


async def _get_or_create_profile(db: AsyncSession, user_id: uuid.UUID, default_name: str) -> Profile:
    profile = await db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is None:
        profile = Profile(
            user_id=user_id,
            display_name=default_name,
            character_config={"onboarding_required": True},
        )
        db.add(profile)
        await db.flush()
    else:
        character = _single_from_config(profile.character_config)
        if character is not None:
            profile.character_config = character.model_dump()
        elif not profile.character_config or not profile.character_config.get("onboarding_required"):
            profile.character_config = {"onboarding_required": True}
    return profile


def _response(profile: Profile) -> ProfileResponse:
    character = _single_from_config(profile.character_config)
    return ProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        character=character,
        onboarding_required=character is None,
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
    if payload.character is not None:
        profile.character_config = payload.character.model_dump()
    elif payload.characters is not None:
        # Compatibility path for the previous pair client: keep one personal character.
        profile.character_config = payload.characters.feminine.model_dump()
    profile.locale = payload.locale
    profile.result_visibility = payload.result_visibility
    profile.sound_enabled = payload.sound_enabled
    profile.haptic_enabled = payload.haptic_enabled
    await db.commit()
    return _response(profile)
