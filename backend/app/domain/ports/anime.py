from __future__ import annotations

import uuid
from typing import Protocol

from ..entities import Anime


class AnimeRepository(Protocol):
    async def get_by_id(self, anime_id: uuid.UUID) -> Anime | None: ...

