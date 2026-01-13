import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ...background import Job, default_job_runner
from ...crud.favorite import remove_favorite as crud_remove_favorite
from ...database import AsyncSessionLocal


async def _apply_remove_favorite(
    user_id: uuid.UUID, anime_id: uuid.UUID
) -> None:
    async with AsyncSessionLocal() as session:
        try:
            await crud_remove_favorite(session, user_id, anime_id)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def remove_favorite(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> None:
    job = Job(
        key=f"favorite:remove:{user_id}:{anime_id}",
        handler=lambda: _apply_remove_favorite(user_id, anime_id),
    )
    await default_job_runner.enqueue(job)
