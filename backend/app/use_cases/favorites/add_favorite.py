import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ...crud.anime import get_anime_by_id
from ...crud.favorite import add_favorite as crud_add_favorite
from ...errors import AppError, ConflictError, NotFoundError
from ...models.favorite import Favorite


async def add_favorite(
    session: AsyncSession, user_id: uuid.UUID, anime_id: uuid.UUID
) -> Favorite:
    try:
        anime = await get_anime_by_id(session, anime_id)
        if anime is None:
            raise NotFoundError("Anime not found")

        favorite = await crud_add_favorite(session, user_id, anime_id)
        await session.commit()
        await session.refresh(favorite)
        return favorite
    except IntegrityError:
        await session.rollback()
        raise ConflictError("Favorite already exists") from None
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
