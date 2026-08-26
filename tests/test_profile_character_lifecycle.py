import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-that-is-at-least-32-chars")

from app.api.profile import CharacterPair, _single_from_config
from app.services.character import DEFAULT_CHARACTER, MASCULINE_CHARACTER


def test_empty_profile_requires_character_onboarding():
    assert _single_from_config({"onboarding_required": True}) is None
    assert _single_from_config({}) is None
    assert _single_from_config(None) is None


def test_legacy_pair_migrates_to_one_feminine_character():
    pair = CharacterPair(feminine=DEFAULT_CHARACTER, masculine=MASCULINE_CHARACTER)

    character = _single_from_config(pair.model_dump())

    assert character is not None
    assert character.gender == "feminine"
    assert character.model_dump() == DEFAULT_CHARACTER.model_dump()


def test_legacy_single_masculine_character_is_preserved():
    character = _single_from_config(MASCULINE_CHARACTER.model_dump())

    assert character is not None
    assert character.gender == "masculine"
    assert character.hair_style == MASCULINE_CHARACTER.hair_style


def test_invalid_character_config_requires_onboarding_again():
    assert _single_from_config({"gender": "unknown", "hair_style": "invalid"}) is None
