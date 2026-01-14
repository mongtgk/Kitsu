from datetime import datetime, timezone

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.refresh_token import get_refresh_token_by_hash
from ...errors import AppError, AuthError, PermissionError
from ...utils.rate_limit import RATE_LIMIT_MESSAGE, auth_rate_limiter, make_key
from ...utils.security import hash_refresh_token
from .register_user import AuthTokens, issue_tokens


REFRESH_TOKEN_IDENTIFIER_LENGTH = 16


def _rate_limit_key(token_hash: str, client_ip: str | None) -> str:
    token_identifier = token_hash[:REFRESH_TOKEN_IDENTIFIER_LENGTH]
    ip_component = client_ip or "unknown-ip"
    return make_key("refresh", ip_component, token_identifier)


def _rate_limit_error() -> AppError:
    return AppError(
        RATE_LIMIT_MESSAGE,
        code="RATE_LIMITED",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )


async def _validate_and_issue_tokens(
    session: AsyncSession, token_hash: str
) -> AuthTokens:
    stored_token = await get_refresh_token_by_hash(session, token_hash, for_update=True)
    if stored_token is None:
        raise AuthError()
    if stored_token.revoked:
        raise PermissionError()
    if stored_token.expires_at <= datetime.now(timezone.utc):
        raise AuthError()
    return await issue_tokens(session, stored_token.user_id)


async def refresh_session(
    session: AsyncSession, refresh_token: str, *, client_ip: str | None = None
) -> AuthTokens:
    token_hash = hash_refresh_token(refresh_token)
    key = _rate_limit_key(token_hash, client_ip)
    if auth_rate_limiter.is_limited(key):
        raise _rate_limit_error()

    try:
        tokens = await _validate_and_issue_tokens(session, token_hash)
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
