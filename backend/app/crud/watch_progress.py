import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.watch_progress import WatchProgress


async def get_watch_progress(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> WatchProgress | None:
    stmt = select(WatchProgress).where(
        WatchProgress.user_id == user_id, WatchProgress.anime_id == anime_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_watch_progress(
    session: AsyncSession,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    episode: int,
    position_seconds: int | None,
    progress_percent: float | None,
) -> WatchProgress:
    progress = WatchProgress(
        user_id=user_id,
        anime_id=anime_id,
        episode=episode,
        position_seconds=position_seconds,
        progress_percent=progress_percent,
    )
    session.add(progress)
    await session.flush()
    return progress


async def update_watch_progress(
    session: AsyncSession,
    progress: WatchProgress,
    episode: int,
    position_seconds: int | None,
    progress_percent: float | None,
) -> WatchProgress:
    progress.episode = episode
    progress.position_seconds = position_seconds
    progress.progress_percent = progress_percent
    await session.flush()
    return progress


async def list_watch_progress(
    session: AsyncSession, user_id: uuid.UUID, limit: int
) -> list[WatchProgress]:
    stmt = (
        select(WatchProgress)
        .where(WatchProgress.user_id == user_id)
        .order_by(WatchProgress.last_watched_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
