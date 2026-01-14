from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.user import get_user_by_email
from ...errors import AppError, AuthError, PermissionError
from ...utils.rate_limit import RATE_LIMIT_MESSAGE, auth_rate_limiter, make_key
from ...utils.security import verify_password
from .register_user import AuthTokens, issue_tokens


def _rate_limit_key(email: str, client_ip: str | None) -> str:
    ip_component = client_ip or "unknown-ip"
    return make_key("login", ip_component, email.lower())


def _rate_limit_error() -> AppError:
    return AppError(
        RATE_LIMIT_MESSAGE,
        code="RATE_LIMITED",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


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
    key = _rate_limit_key(email, client_ip)
    if auth_rate_limiter.is_limited(key):
        raise _rate_limit_error()

    try:
        tokens = await _authenticate_user(session, email, password)
    except (AuthError, PermissionError):
        auth_rate_limiter.record_failure(key)
        await session.rollback()
        raise
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
    auth_rate_limiter.reset(key)
    return tokens
