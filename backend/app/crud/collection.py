from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.collection import Collection


async def create_collection(session: AsyncSession, data: dict) -> Collection:
    collection = Collection(**data)
    session.add(collection)
    await session.flush()
    return collection


async def list_collections(
    session: AsyncSession, limit: int = 20, offset: int = 0
) -> list[Collection]:
    stmt = select(Collection).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())
