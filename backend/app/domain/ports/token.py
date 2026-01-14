from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from ..entities import RefreshToken


class TokenRepository(Protocol):
    async def save_or_rotate(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken: ...

    async def get_by_hash(
        self, token_hash: str, *, for_update: bool = False
    ) -> RefreshToken | None: ...

    async def revoke_for_user(self, user_id: uuid.UUID) -> None: ...

