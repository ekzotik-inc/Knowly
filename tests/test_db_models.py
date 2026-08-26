import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.models import Base


@pytest.mark.asyncio
async def test_all_models_can_be_created_on_test_database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()
