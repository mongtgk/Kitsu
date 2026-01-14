from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.auth_rate_limit import (
    RATE_LIMIT_MESSAGE,
    RateLimitExceededError,
    check_login_rate_limit,
    record_login_failure,
    reset_login_limit,
)
from ...crud.user import get_user_by_email
from ...errors import AppError, AuthError, PermissionError
from ...utils.security import verify_password
from .register_user import AuthTokens, issue_tokens


async def _authenticate_user(
    session: AsyncSession, email: str, password: str
) -> AuthTokens:
    user = await get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError()
    return await issue_tokens(session, user.id)


async def login_user(
    session: AsyncSession, email: str, password: str, *, client_ip: str | None = None
) -> AuthTokens:
    try:
        key = check_login_rate_limit(email, client_ip)
    except RateLimitExceededError:
        raise AppError(
            RATE_LIMIT_MESSAGE,
            code="RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        ) from None

    try:
        tokens = await _authenticate_user(session, email, password)
    except (AuthError, PermissionError):
        record_login_failure(key)
        await session.rollback()
        raise
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
    reset_login_limit(key)
    return tokens
