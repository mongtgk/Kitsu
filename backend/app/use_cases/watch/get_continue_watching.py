import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.watch_progress import list_watch_progress
from ...models.watch_progress import WatchProgress


async def get_continue_watching(
    session: AsyncSession, user_id: uuid.UUID, limit: int
) -> list[WatchProgress]:
    return await list_watch_progress(session, user_id=user_id, limit=limit)
