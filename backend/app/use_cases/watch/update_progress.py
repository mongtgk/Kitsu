import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.anime import get_anime_by_id
from ...crud.watch_progress import (
    create_watch_progress,
    get_watch_progress,
    update_watch_progress as crud_update_watch_progress,
)
from ...errors import AppError, NotFoundError, ValidationError
from ...models.watch_progress import WatchProgress


async def update_progress(
    session: AsyncSession,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    episode: int,
    position_seconds: int | None = None,
    progress_percent: float | None = None,
) -> WatchProgress:
    try:
        if episode <= 0:
            raise ValidationError("Episode number must be positive")
        if position_seconds is None and progress_percent is None:
            raise ValidationError(
                "Either position_seconds or progress_percent must be provided"
            )
        if progress_percent is not None and not (0 <= progress_percent <= 100):
            raise ValidationError("Progress percent must be between 0 and 100")
        if position_seconds is not None and position_seconds < 0:
            raise ValidationError("Position in seconds must be non-negative")

        anime = await get_anime_by_id(session, anime_id)
        if anime is None:
            raise NotFoundError("Anime not found")

        progress = await get_watch_progress(session, user_id, anime_id)
        if progress:
            progress = await crud_update_watch_progress(
                session, progress, episode, position_seconds, progress_percent
            )
        else:
            progress = await create_watch_progress(
                session, user_id, anime_id, episode, position_seconds, progress_percent
            )

        await session.commit()
        await session.refresh(progress)
        return progress
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
