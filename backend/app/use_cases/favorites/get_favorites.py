import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.favorite import list_favorites
from ...models.favorite import Favorite


async def get_favorites(
    session: AsyncSession, user_id: uuid.UUID, limit: int, offset: int
) -> list[Favorite]:
    return await list_favorites(session, user_id=user_id, limit=limit, offset=offset)
