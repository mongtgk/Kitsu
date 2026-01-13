from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.helpers import require_any_permission, require_permission
from ..dependencies import get_db

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get(
    "/",
    dependencies=[Depends(require_any_permission(["read:content"]))],
)
async def list_collections(db: AsyncSession = Depends(get_db)) -> list[dict]:
    # TODO: Replace with collection retrieval.
    return []


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("write:content"))],
)
async def create_collection(db: AsyncSession = Depends(get_db)) -> dict:
    # TODO: Persist collection to database.
    return {"message": "collection created"}
