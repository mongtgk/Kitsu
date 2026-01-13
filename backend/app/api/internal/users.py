from fastapi import APIRouter

from ...routers import users as base_users

router = APIRouter()
router.include_router(base_users.router)
