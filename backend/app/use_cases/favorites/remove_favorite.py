import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.favorite import remove_favorite as crud_remove_favorite
from ...errors import AppError


async def remove_favorite(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> None:
    try:
        await crud_remove_favorite(session, user_id, anime_id)
        await session.commit()
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
