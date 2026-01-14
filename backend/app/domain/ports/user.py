from __future__ import annotations

from typing import Protocol

from ..entities import User


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, email: str, password_hash: str) -> User: ...

