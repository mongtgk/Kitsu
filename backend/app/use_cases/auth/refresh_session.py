from datetime import datetime, timezone

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.auth_rate_limit import (
    RATE_LIMIT_MESSAGE,
    RateLimitExceededError,
    check_refresh_rate_limit,
    record_refresh_failure,
    reset_refresh_limit,
)
from ...crud.refresh_token import get_refresh_token_by_hash
from ...errors import AppError, AuthError, PermissionError
from ...security.token_inspection import InvalidTokenError, validate_refresh_token
from .register_user import AuthTokens, issue_tokens


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
    try:
        token_hash = validate_refresh_token(refresh_token)
    except InvalidTokenError:
        raise AuthError() from None

    token_identifier = token_hash[:16]
    try:
        key = check_refresh_rate_limit(token_identifier, client_ip)
    except RateLimitExceededError:
        raise AppError(
            RATE_LIMIT_MESSAGE,
            code="RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        ) from None

    try:
        tokens = await _validate_and_issue_tokens(session, token_hash)
    except (AuthError, PermissionError):
        record_refresh_failure(key)
        await session.rollback()
        raise
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
    reset_refresh_limit(key)
    return tokens
