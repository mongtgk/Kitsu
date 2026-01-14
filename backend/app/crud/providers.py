from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from ..application.repositories import RepositoryFactory, RepositoryProvider
from ..database import AsyncSessionLocal
from .repositories import (
    SqlAlchemyAnimeRepository,
    SqlAlchemyFavoriteRepository,
    SqlAlchemyTokenRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyWatchProgressRepository,
)


def build_repository_provider(session: AsyncSession) -> RepositoryProvider:
    return RepositoryProvider(
        users=SqlAlchemyUserRepository(session),
        tokens=SqlAlchemyTokenRepository(session),
        anime=SqlAlchemyAnimeRepository(session),
        favorites=SqlAlchemyFavoriteRepository(session),
        watch_progress=SqlAlchemyWatchProgressRepository(session),
    )


@asynccontextmanager
async def repository_provider_factory() -> AsyncIterator[RepositoryProvider]:
    async with AsyncSessionLocal() as session:
        provider = build_repository_provider(session)
        yield provider


def get_repository_factory() -> RepositoryFactory:
    return repository_provider_factory

