from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncContextManager, Protocol

from ..domain.ports.anime import AnimeRepository
from ..domain.ports.favorite import FavoriteRepository
from ..domain.ports.token import TokenRepository
from ..domain.ports.user import UserRepository
from ..domain.ports.watch_progress import WatchProgressRepository


@dataclass
class RepositoryProvider:
    users: UserRepository
    tokens: TokenRepository
    anime: AnimeRepository
    favorites: FavoriteRepository
    watch_progress: WatchProgressRepository


class RepositoryFactory(Protocol):
    def __call__(self) -> AsyncContextManager[RepositoryProvider]: ...
