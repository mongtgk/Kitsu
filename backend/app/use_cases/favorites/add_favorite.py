import uuid
from datetime import datetime, timezone

from ...application.repositories import RepositoryFactory, RepositoryProvider
from ...background import Job, default_job_runner
from ...errors import ConflictError, NotFoundError
from ...schemas.favorite import FavoriteRead


async def _apply_add_favorite(
    repos: RepositoryProvider,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    favorite_id: uuid.UUID,
    created_at: datetime,
) -> None:
    anime = await repos.anime.get_by_id(anime_id)
    if anime is None:
        raise NotFoundError("Anime not found")

    existing = await repos.favorites.get(user_id, anime_id)
    if existing is None:
        await repos.favorites.add(
            user_id,
            anime_id,
            favorite_id=favorite_id,
            created_at=created_at,
        )


async def persist_add_favorite(
    repo_factory: RepositoryFactory,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    favorite_id: uuid.UUID,
    created_at: datetime,
) -> None:
    async with repo_factory() as repos:
        await _apply_add_favorite(repos, user_id, anime_id, favorite_id, created_at)


async def add_favorite(
    repos: RepositoryProvider,
    repo_factory: RepositoryFactory,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
) -> FavoriteRead:
    anime = await repos.anime.get_by_id(anime_id)
    if anime is None:
        raise NotFoundError("Anime not found")

    existing = await repos.favorites.get(user_id, anime_id)
    if existing:
        raise ConflictError("Favorite already exists")

    favorite_id = uuid.uuid4()
    created_at = datetime.now(timezone.utc)
    result = FavoriteRead(id=favorite_id, anime_id=anime_id, created_at=created_at)

    async def handler() -> None:
        await persist_add_favorite(repo_factory, user_id, anime_id, favorite_id, created_at)

    job = Job(key=f"favorite:add:{user_id}:{anime_id}", handler=handler)
    await default_job_runner.enqueue(job)
    return result
