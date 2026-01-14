from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from ..entities import Favorite


class FavoriteRepository(Protocol):
    async def get(self, user_id: uuid.UUID, anime_id: uuid.UUID) -> Favorite | None: ...

    async def add(
        self,
        user_id: uuid.UUID,
        anime_id: uuid.UUID,
        *,
        favorite_id: uuid.UUID | None = None,
        created_at: datetime | None = None,
    ) -> Favorite: ...

    async def remove(self, user_id: uuid.UUID, anime_id: uuid.UUID) -> bool: ...

    async def list_for_user(
        self, user_id: uuid.UUID, limit: int, offset: int
    ) -> list[Favorite]: ...
