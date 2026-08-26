from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Personality = Literal["cute", "funny", "romantic", "confident", "mysterious", "chaotic"]
Emotion = Literal[
    "default", "playful", "love", "shy", "happy", "surprise", "sad",
    "mischievous", "thinking", "proud", "shocked", "excited",
]


class CharacterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gender: Literal["feminine", "masculine", "neutral"] = "feminine"
    personality: Personality = "romantic"
    head_shape: Literal["round", "soft", "sharp"] = "soft"
    skin_tone: Literal["porcelain", "peach", "honey", "almond", "cocoa"] = "peach"
    hair_style: Literal["short", "bob", "long", "curly", "bun"] = "bob"
    hair_color: Literal["midnight", "chestnut", "honey", "rose", "lavender"] = "chestnut"
    eyes: Literal["round", "soft", "sparkle", "mischief"] = "soft"
    brows: Literal["soft", "arched", "straight", "bold"] = "soft"
    outfit: Literal["hoodie", "sweater", "shirt", "dress", "jacket"] = "sweater"
    accessory: Literal["none", "heart", "star", "flower", "sparkle"] = "heart"
    glasses: Literal["none", "round", "cat_eye"] = "none"
    hat: Literal["none", "beanie", "beret", "halo"] = "none"
    palette: Literal["rose", "violet", "mint", "sunset", "night"] = "rose"


DEFAULT_CHARACTER = CharacterConfig()
MASCULINE_CHARACTER = CharacterConfig(
    gender="masculine",
    personality="confident",
    head_shape="sharp",
    skin_tone="honey",
    hair_style="short",
    hair_color="midnight",
    eyes="mischief",
    brows="bold",
    outfit="jacket",
    accessory="star",
    palette="night",
)


class CharacterState(BaseModel):
    emotion: Emotion = "default"
    pose: Literal["idle", "bounce", "cover", "victory", "tilt", "wink"] = "idle"
    line: str = Field(max_length=160)


PERSONALITY_LINES: dict[Personality, dict[str, str]] = {
    "cute": {"correct": "Ой, ты правда внимательно слушал 🥺", "wrong": "Ой... почти угадал 🥺", "create": "Давай сделаем что-нибудь очень милое 💗"},
    "funny": {"correct": "Вот это попадание! Я всё записал 😂", "wrong": "Ну всё. Я запомнил этот ответ 😂", "create": "Сейчас устроим тест, который никто не забудет 😂"},
    "romantic": {"correct": "Ого. А ты внимательно слушал ❤️", "wrong": "Кажется, здесь ты промахнулся 😏", "create": "Добавим немного магии и сердечек 💗"},
    "confident": {"correct": "Именно так. Стиль узнаётся сразу 😎", "wrong": "Смелая версия, но не сегодня 😎", "create": "Сделаем тест, который выдержит любой вызов 😎"},
    "mysterious": {"correct": "Интересно... ты видишь меня насквозь 👀", "wrong": "Интересно... я ожидал другого 👀", "create": "Оставим пару загадок между строк 👀"},
    "chaotic": {"correct": "АХАХА, ДА! Как ты это узнал?! 😈", "wrong": "АХАХА, НЕТ 😈", "create": "Пристегнись. Будет немного хаоса 😈"},
}


def character_for_event(personality: Personality, event: str, *, streak: int = 0, percentage: int | None = None) -> CharacterState:
    lines = PERSONALITY_LINES[personality]
    if event == "correct":
        if streak >= 5:
            return CharacterState(emotion="excited", pose="bounce", line="Пять подряд! Ты читаешь мои мысли 🔥")
        return CharacterState(emotion="happy", pose="bounce", line=lines["correct"])
    if event == "wrong":
        return CharacterState(emotion="sad", pose="cover", line=lines["wrong"])
    if event == "create":
        return CharacterState(emotion="playful", pose="wink", line=lines["create"])
    if event == "result":
        score = percentage or 0
        if score >= 95:
            return CharacterState(emotion="excited", pose="victory", line="95%+?! Это уже чтение мыслей 🔥")
        if score >= 81:
            return CharacterState(emotion="proud", pose="victory", line="Ого. Это уже серьёзно 🥰")
        if score < 41:
            return CharacterState(emotion="thinking", pose="tilt", line="Хм... у нас ещё есть что открыть 👀")
        return CharacterState(emotion="proud", pose="idle", line="Неплохо. Мы становимся ближе 💗")
    return CharacterState(emotion="default", pose="idle", line="Посмотрим, действительно ли ты меня знаешь 👀")
