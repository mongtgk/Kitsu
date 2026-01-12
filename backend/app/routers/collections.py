from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/")
async def list_collections(db: AsyncSession = Depends(get_db)) -> list[dict]:
    # TODO: Replace with collection retrieval.
    return []


@router.post("/", status_code=201)
async def create_collection(db: AsyncSession = Depends(get_db)) -> dict:
    # TODO: Persist collection to database.
    return {"message": "collection created"}

