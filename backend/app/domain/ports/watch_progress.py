from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from ..entities import WatchProgress


class WatchProgressRepository(Protocol):
    async def get(self, user_id: uuid.UUID, anime_id: uuid.UUID) -> WatchProgress | None: ...

    async def list_for_user(self, user_id: uuid.UUID, limit: int) -> list[WatchProgress]: ...

    async def upsert(
        self,
        user_id: uuid.UUID,
        anime_id: uuid.UUID,
        episode: int,
        position_seconds: int | None,
        progress_percent: float | None,
        *,
        progress_id: uuid.UUID,
        created_at: datetime,
        last_watched_at: datetime,
    ) -> WatchProgress: ...
