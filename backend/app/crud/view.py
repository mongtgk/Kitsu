from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.view import View


async def record_view(session: AsyncSession, data: dict) -> View:
    view = View(**data)
    session.add(view)
    await session.flush()
    return view


async def list_views(
    session: AsyncSession, limit: int = 20, offset: int = 0
) -> list[View]:
    stmt = select(View).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())
