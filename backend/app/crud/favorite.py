import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.favorite import Favorite


async def get_favorite(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> Favorite | None:
    stmt = select(Favorite).where(
        Favorite.user_id == user_id, Favorite.anime_id == anime_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_favorite(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> Favorite:
    favorite = Favorite(user_id=user_id, anime_id=anime_id)
    session.add(favorite)
    await session.flush()
    return favorite


async def remove_favorite(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> bool:
    favorite = await get_favorite(session, user_id, anime_id)
    if favorite is None:
        return False

    session.delete(favorite)
    await session.flush()
    return True


async def list_favorites(
    session: AsyncSession, user_id: uuid.UUID, limit: int, offset: int
) -> list[Favorite]:
    stmt = (
        select(Favorite)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
