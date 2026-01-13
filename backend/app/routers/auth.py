import ipaddress

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db
from ..errors import AppError, AuthError, PermissionError
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
from ..utils.rate_limit import auth_rate_limiter, make_key
from ..utils.security import hash_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


REFRESH_TOKEN_IDENTIFIER_LENGTH = 16


def _client_ip(request: Request) -> str:
    client_host = request.client.host if request.client else None
    if client_host:
        try:
            parsed = ipaddress.ip_address(client_host)
            if not parsed.is_private and not parsed.is_loopback:
                return client_host
        except ValueError:
            return client_host

    forwarded_for = request.headers.get("x-real-ip") or request.headers.get(
        "x-forwarded-for"
    )
    if forwarded_for:
        forwarded_ip = forwarded_for.split(",")[0].strip()
        if forwarded_ip:
            return forwarded_ip

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
    client_ip = _client_ip(request)
    key = make_key("login", client_ip, payload.email.lower())
    if auth_rate_limiter.is_limited(key):
        raise AppError(
            "Too many attempts, try again later",
            code="RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    try:
        tokens = await login_user(db, payload.email, payload.password)
    except (AuthError, PermissionError):
        auth_rate_limiter.record_failure(key)
        raise
    auth_rate_limiter.reset(key)
    return TokenResponse(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    client_ip = _client_ip(request)
    token_identifier = hash_refresh_token(payload.refresh_token)[
        :REFRESH_TOKEN_IDENTIFIER_LENGTH
    ]
    key = make_key("refresh", client_ip, token_identifier)
    if auth_rate_limiter.is_limited(key):
        raise AppError(
            "Too many attempts, try again later",
            code="RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    try:
        tokens = await refresh_session(db, payload.refresh_token)
    except (AuthError, PermissionError):
        auth_rate_limiter.record_failure(key)
        raise
    auth_rate_limiter.reset(key)
    return TokenResponse(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest, db: AsyncSession = Depends(get_db)
) -> None:
    await logout_user(db, payload.refresh_token)
