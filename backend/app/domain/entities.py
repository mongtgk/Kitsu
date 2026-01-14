import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: uuid.UUID
    email: str
    password_hash: str
    is_active: bool = True
    created_at: datetime | None = None


@dataclass(frozen=True)
class RefreshToken:
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    revoked: bool


@dataclass(frozen=True)
class Anime:
    id: uuid.UUID


@dataclass(frozen=True)
class Favorite:
    id: uuid.UUID
    user_id: uuid.UUID
    anime_id: uuid.UUID
    created_at: datetime


@dataclass(frozen=True)
class WatchProgress:
    id: uuid.UUID
    user_id: uuid.UUID
    anime_id: uuid.UUID
    episode: int
    position_seconds: int | None
    progress_percent: float | None
    created_at: datetime
    last_watched_at: datetime

