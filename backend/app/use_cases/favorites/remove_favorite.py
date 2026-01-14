import uuid

from ...application.repositories import RepositoryFactory, RepositoryProvider
from ...background import Job, default_job_runner


async def persist_remove_favorite(
    repo_factory: RepositoryFactory, user_id: uuid.UUID, anime_id: uuid.UUID
) -> None:
    async with repo_factory() as repos:
        await repos.favorites.remove(user_id, anime_id)


async def remove_favorite(
    repos: RepositoryProvider, repo_factory: RepositoryFactory, user_id: uuid.UUID, anime_id: uuid.UUID
) -> None:
    async def handler() -> None:
        await persist_remove_favorite(repo_factory, user_id, anime_id)

    job = Job(
        key=f"favorite:remove:{user_id}:{anime_id}",
        handler=handler,
    )
    await default_job_runner.enqueue(job)
