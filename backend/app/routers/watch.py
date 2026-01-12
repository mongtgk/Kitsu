from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..schemas.watch import WatchProgressRead, WatchProgressUpdate
from ..use_cases.watch import get_continue_watching, update_progress

router = APIRouter(prefix="/watch", tags=["watch"])


@router.post("/progress", response_model=WatchProgressRead)
async def upsert_progress(
    payload: WatchProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WatchProgressRead:
    return await update_progress(
        db,
        user_id=current_user.id,
        anime_id=payload.anime_id,
        episode=payload.episode,
        position_seconds=payload.position_seconds,
        progress_percent=payload.progress_percent,
    )


@router.get("/continue", response_model=list[WatchProgressRead])
async def continue_watching(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WatchProgressRead]:
    return await get_continue_watching(db, user_id=current_user.id, limit=limit)
