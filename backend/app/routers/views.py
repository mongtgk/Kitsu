from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/")
async def list_views(db: AsyncSession = Depends(get_db)) -> list[dict]:
    # TODO: Replace with view history retrieval.
    return []


@router.post("/", status_code=201)
async def create_view(db: AsyncSession = Depends(get_db)) -> dict:
    # TODO: Persist view record.
    return {"message": "view recorded"}

