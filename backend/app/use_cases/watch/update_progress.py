import uuid
from datetime import datetime, timezone

from ...application.repositories import RepositoryFactory, RepositoryProvider
from ...background import Job, default_job_runner
from ...errors import NotFoundError, ValidationError
from ...schemas.watch import WatchProgressRead


def _validate_update_request(
    episode: int, position_seconds: int | None, progress_percent: float | None
) -> None:
    if episode <= 0:
        raise ValidationError("Episode number must be positive")
    if position_seconds is None and progress_percent is None:
        raise ValidationError("Either position_seconds or progress_percent must be provided")
    if progress_percent is not None and not (0 <= progress_percent <= 100):
        raise ValidationError("Progress percent must be between 0 and 100")
    if position_seconds is not None and position_seconds < 0:
        raise ValidationError("Position in seconds must be non-negative")


async def _apply_watch_progress(
    repos: RepositoryProvider,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    episode: int,
    position_seconds: int | None,
    progress_percent: float | None,
    *,
    progress_id: uuid.UUID,
    created_at: datetime,
    last_watched_at: datetime,
) -> None:
    anime = await repos.anime.get_by_id(anime_id)
    if anime is None:
        raise NotFoundError("Anime not found")

    await repos.watch_progress.upsert(
        user_id,
        anime_id,
        episode,
        position_seconds,
        progress_percent,
        progress_id=progress_id,
        created_at=created_at,
        last_watched_at=last_watched_at,
    )


async def persist_update_progress(
    repo_factory: RepositoryFactory,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    episode: int,
    position_seconds: int | None,
    progress_percent: float | None,
    *,
    progress_id: uuid.UUID,
    created_at: datetime,
    last_watched_at: datetime,
) -> None:
    async with repo_factory() as repos:
        await _apply_watch_progress(
            repos,
            user_id,
            anime_id,
            episode,
            position_seconds,
            progress_percent,
            progress_id=progress_id,
            created_at=created_at,
            last_watched_at=last_watched_at,
        )


async def update_progress(
    repos: RepositoryProvider,
    repo_factory: RepositoryFactory,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    episode: int,
    position_seconds: int | None = None,
    progress_percent: float | None = None,
) -> WatchProgressRead:
    _validate_update_request(episode, position_seconds, progress_percent)

    anime = await repos.anime.get_by_id(anime_id)
    if anime is None:
        raise NotFoundError("Anime not found")

    existing_progress = await repos.watch_progress.get(user_id, anime_id)
    now = datetime.now(timezone.utc)
    progress_id = existing_progress.id if existing_progress else uuid.uuid4()
    created_at = existing_progress.created_at if existing_progress else now

    result = WatchProgressRead(
        id=progress_id,
        anime_id=anime_id,
        episode=episode,
        position_seconds=position_seconds,
        progress_percent=progress_percent,
        created_at=created_at,
        last_watched_at=now,
    )

    async def handler() -> None:
        await persist_update_progress(
            repo_factory,
            user_id,
            anime_id,
            episode,
            position_seconds,
            progress_percent,
            progress_id=progress_id,
            created_at=created_at,
            last_watched_at=result.last_watched_at,
        )

    job = Job(
        key=(
            f"watch-progress:{user_id}:{anime_id}:episode={episode}:"
            f"position={position_seconds if position_seconds is not None else 'none'}:"
            f"percent={progress_percent if progress_percent is not None else 'none'}"
        ),
        handler=handler,
    )
    await default_job_runner.enqueue(job)
    return result
