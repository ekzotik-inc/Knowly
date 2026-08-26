from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AnalyticsEvent


async def record_event(
    db: AsyncSession,
    *,
    event_name: str,
    actor_user_id: uuid.UUID | None = None,
    test_id: uuid.UUID | None = None,
    event_metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        AnalyticsEvent(
            event_name=event_name,
            actor_user_id=actor_user_id,
            test_id=test_id,
            event_metadata=event_metadata or {},
        )
    )
