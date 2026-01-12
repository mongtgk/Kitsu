from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserRead
from ..utils.files import delete_avatar_file, save_avatar_file

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_current_user_profile(
    avatar: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    if avatar is None:
        return current_user

    previous_avatar = current_user.avatar
    try:
        new_avatar_path = await save_avatar_file(avatar)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    current_user.avatar = new_avatar_path
    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        delete_avatar_file(new_avatar_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update profile.",
        ) from exc
    await db.refresh(current_user)

    if previous_avatar:
        delete_avatar_file(previous_avatar)
    return current_user


@router.get("/", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[UserRead]:
    # TODO: Replace with real database query.
    return []


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    # TODO: Persist user to database.
    return UserRead(id=0, email=payload.email, is_active=True, created_at=datetime.now())


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> UserRead:
    # TODO: Load user from database.
    return UserRead(
        id=user_id,
        email="placeholder@example.com",
        is_active=True,
        created_at=datetime.now(),
    )
