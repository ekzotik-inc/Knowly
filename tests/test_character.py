import pytest

from app.services.character import character_for_event


@pytest.mark.parametrize("personality", ["cute", "funny", "romantic", "confident", "mysterious", "chaotic"])
def test_every_personality_has_contextual_lines(personality):
    correct = character_for_event(personality, "correct")
    wrong = character_for_event(personality, "wrong")
    creating = character_for_event(personality, "create")

    assert correct.emotion == "happy"
    assert correct.pose == "bounce"
    assert wrong.emotion == "sad"
    assert wrong.pose == "cover"
    assert creating.emotion == "playful"
    assert creating.pose == "wink"
    assert all(item.line for item in (correct, wrong, creating))


def test_five_correct_answers_trigger_excited_state():
    state = character_for_event("romantic", "correct", streak=5)
    assert state.emotion == "excited"
    assert state.pose == "bounce"
    assert "Пять" in state.line


@pytest.mark.parametrize(
    ("percentage", "emotion", "pose"),
    [(95, "excited", "victory"), (87, "proud", "victory"), (35, "thinking", "tilt"), (70, "proud", "idle")],
)
def test_result_percentage_selects_emotion_and_pose(percentage, emotion, pose):
    state = character_for_event("romantic", "result", percentage=percentage)
    assert state.emotion == emotion
    assert state.pose == pose


@pytest.mark.parametrize("gender", ["feminine", "masculine", "neutral"])
def test_character_config_accepts_all_gender_variants(gender):
    from app.services.character import CharacterConfig

    config = CharacterConfig(gender=gender)

    assert config.gender == gender


def test_character_config_rejects_unknown_gender():
    from pydantic import ValidationError
    from app.services.character import CharacterConfig

    with pytest.raises(ValidationError):
        CharacterConfig(gender="unknown")
