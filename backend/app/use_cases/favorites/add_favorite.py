import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ...background import Job, default_job_runner
from ...crud.anime import get_anime_by_id
from ...crud.favorite import add_favorite as crud_add_favorite, get_favorite
from ...database import AsyncSessionLocal
from ...errors import ConflictError, NotFoundError
from ...schemas.favorite import FavoriteRead


async def _apply_add_favorite(
    session: AsyncSession,
    user_id: uuid.UUID,
    anime_id: uuid.UUID,
    favorite_id: uuid.UUID,
    created_at: datetime,
) -> None:
    try:
        anime = await get_anime_by_id(session, anime_id)
        if anime is None:
            raise NotFoundError("Anime not found")

        existing = await get_favorite(session, user_id, anime_id)
        if existing is None:
            await crud_add_favorite(
                session,
                user_id,
                anime_id,
                favorite_id=favorite_id,
                created_at=created_at,
            )
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def add_favorite(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> FavoriteRead:
    anime = await get_anime_by_id(session, anime_id)
    if anime is None:
        raise NotFoundError("Anime not found")

    existing = await get_favorite(session, user_id, anime_id)
    if existing:
        raise ConflictError("Favorite already exists")

    favorite_id = uuid.uuid4()
    created_at = datetime.now(timezone.utc)
    result = FavoriteRead(id=favorite_id, anime_id=anime_id, created_at=created_at)

    async def handler() -> None:
        async with AsyncSessionLocal() as job_session:
            await _apply_add_favorite(
                job_session, user_id, anime_id, favorite_id, created_at
            )

    job = Job(key=f"favorite:add:{user_id}:{anime_id}", handler=handler)
    await default_job_runner.enqueue(job)
    return result
