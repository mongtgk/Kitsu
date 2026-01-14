from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..schemas.auth import (
    LogoutRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
)
from ..use_cases.auth.login_user import login_user
from ..use_cases.auth.logout_user import logout_user
from ..use_cases.auth.refresh_session import refresh_session
from ..use_cases.auth.register_user import register_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    client_host = request.client.host if request.client else None
    return client_host or "unknown-ip"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    tokens = await register_user(db, payload.email, payload.password)
    return TokenResponse(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin, request: Request, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    tokens = await login_user(
        db, payload.email, payload.password, client_ip=_client_ip(request)
    )
    return TokenResponse(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    tokens = await refresh_session(
        db, payload.refresh_token, client_ip=_client_ip(request)
    )
    return TokenResponse(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest, db: AsyncSession = Depends(get_db)
) -> None:
    await logout_user(db, payload.refresh_token)
