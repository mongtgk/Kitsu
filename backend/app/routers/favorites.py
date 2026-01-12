from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..schemas.favorite import FavoriteCreate, FavoriteRead
from ..use_cases.favorites import (
    add_favorite as add_favorite_use_case,
    get_favorites as get_favorites_use_case,
    remove_favorite as remove_favorite_use_case,
)

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/", response_model=list[FavoriteRead])
async def get_favorites(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FavoriteRead]:
    return await get_favorites_use_case(
        db, user_id=current_user.id, limit=limit, offset=offset
    )


@router.post("/", response_model=FavoriteRead, status_code=status.HTTP_201_CREATED)
async def create_favorite(
    payload: FavoriteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteRead:
    return await add_favorite_use_case(
        db, user_id=current_user.id, anime_id=payload.anime_id
    )


@router.delete("/{anime_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(
    anime_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await remove_favorite_use_case(db, user_id=current_user.id, anime_id=anime_id)
