from __future__ import annotations

from sqlalchemy import select, text

from app.db.models import Achievement, Base, Product
from app.db.session import SessionLocal, engine

PRODUCT_SEEDS = (
    {
        "code": "premium_results",
        "title": "Подробный разбор",
        "description": "Открывает детальный разбор ответов",
        "stars": 49,
        "entitlement_key": "premium_results",
    },
    {
        "code": "extra_questions",
        "title": "Расширенный тест",
        "description": "Дополнительные вопросы для теста",
        "stars": 39,
        "entitlement_key": "extra_questions",
    },
    {
        "code": "profile_themes",
        "title": "Темы профиля",
        "description": "Премиальные варианты оформления профиля",
        "stars": 29,
        "entitlement_key": "profile_themes",
    },
)

ACHIEVEMENT_SEEDS = (
    {"code": "heartbreaker", "title": "Heartbreaker", "description": "Создай первый тест", "icon": "♥", "xp_reward": 20},
    {"code": "mind_reader", "title": "Mind Reader", "description": "Заверши первый тест", "icon": "◉", "xp_reward": 30},
    {"code": "bestie", "title": "Bestie", "description": "Получи 100% в тесте", "icon": "★", "xp_reward": 50},
    {"code": "popular", "title": "Popular", "description": "Собери пять прохождений", "icon": "✦", "xp_reward": 60},
    {"code": "trickster", "title": "Trickster", "description": "Добавь сложный вопрос", "icon": "?", "xp_reward": 25},
    {"code": "too_close", "title": "Too Close", "description": "Набери от 80% до 99%", "icon": "≈", "xp_reward": 40},
)


async def initialize_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS correct_options JSON NOT NULL DEFAULT '[]'::json"))
        await connection.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS multiple_answers BOOLEAN NOT NULL DEFAULT FALSE"))
        await connection.execute(text("ALTER TABLE session_answers ADD COLUMN IF NOT EXISTS selected_options JSON NOT NULL DEFAULT '[]'::json"))
        await connection.execute(text("ALTER TABLE result_answers ADD COLUMN IF NOT EXISTS selected_options JSON NOT NULL DEFAULT '[]'::json"))
        await connection.execute(text("ALTER TABLE result_answers ADD COLUMN IF NOT EXISTS correct_options JSON NOT NULL DEFAULT '[]'::json"))
        await connection.execute(text("UPDATE questions SET correct_options = json_build_array(correct_option) WHERE correct_options = '[]'::json"))
        await connection.execute(text("UPDATE session_answers SET selected_options = json_build_array(selected_option) WHERE selected_options = '[]'::json"))
        await connection.execute(text("UPDATE result_answers SET selected_options = json_build_array(selected_option) WHERE selected_options = '[]'::json"))
        await connection.execute(text("UPDATE result_answers SET correct_options = json_build_array(correct_option) WHERE correct_options = '[]'::json"))

    async with SessionLocal() as session:
        for values in PRODUCT_SEEDS:
            exists = await session.scalar(select(Product.id).where(Product.code == values["code"]))
            if exists is None:
                session.add(Product(**values))

        for values in ACHIEVEMENT_SEEDS:
            exists = await session.scalar(select(Achievement.id).where(Achievement.code == values["code"]))
            if exists is None:
                session.add(Achievement(**values))

        await session.commit()
