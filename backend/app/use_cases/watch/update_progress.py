import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ...background import Job, default_job_runner
from ...crud.anime import get_anime_by_id
from ...crud.watch_progress import (
    create_watch_progress,
    get_watch_progress,
    update_watch_progress as crud_update_watch_progress,
)
from ...database import AsyncSessionLocal
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
    session: AsyncSession,
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
    try:
        anime = await get_anime_by_id(session, anime_id)
        if anime is None:
            raise NotFoundError("Anime not found")

        progress = await get_watch_progress(session, user_id, anime_id)
        if progress:
            await crud_update_watch_progress(
                session,
                progress,
                episode,
                position_seconds,
                progress_percent,
                last_watched_at=last_watched_at,
            )
        else:
            await create_watch_progress(
                session,
                user_id,
                anime_id,
                episode,
                position_seconds,
                progress_percent,
                progress_id=progress_id,
                created_at=created_at,
                last_watched_at=last_watched_at,
            )

        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def update_progress(
    session: AsyncSession,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    episode: int,
    position_seconds: int | None = None,
    progress_percent: float | None = None,
) -> WatchProgressRead:
    _validate_update_request(episode, position_seconds, progress_percent)

    anime = await get_anime_by_id(session, anime_id)
    if anime is None:
        raise NotFoundError("Anime not found")

    existing_progress = await get_watch_progress(session, user_id, anime_id)
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
        async with AsyncSessionLocal() as job_session:
            await _apply_watch_progress(
                job_session,
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
        key=f"watch-progress:{user_id}:{anime_id}:{episode}:{position_seconds}:{progress_percent}",
        handler=handler,
    )
    await default_job_runner.enqueue(job)
    return result
