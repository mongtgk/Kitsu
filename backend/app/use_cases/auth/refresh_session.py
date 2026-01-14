from datetime import datetime, timezone

from ...application.auth_rate_limit import (
    RATE_LIMIT_MESSAGE,
    RateLimitExceededError,
    check_refresh_rate_limit,
    record_refresh_failure,
    reset_refresh_limit,
)
from ...domain.ports.token import TokenRepository
from ...errors import (
    AuthenticationError,
    PermissionDenied,
    RateLimitExceeded,
)
from ...security.token_inspection import InvalidTokenError, validate_refresh_token
from .register_user import AuthTokens, issue_tokens


REFRESH_TOKEN_IDENTIFIER_LENGTH = 16


async def _validate_and_issue_tokens(
    token_repo: TokenRepository, token_hash: str
) -> AuthTokens:
    stored_token = await token_repo.get_by_hash(token_hash, for_update=True)
    if stored_token is None:
        raise AuthenticationError()
    if stored_token.revoked:
        raise PermissionDenied()
    if stored_token.expires_at <= datetime.now(timezone.utc):
        raise AuthenticationError()
    return await issue_tokens(token_repo, stored_token.user_id)


async def refresh_session(
    token_repo: TokenRepository, refresh_token: str, *, client_ip: str | None = None
) -> AuthTokens:
    try:
        token_hash = validate_refresh_token(refresh_token)
    except InvalidTokenError:
        raise AuthenticationError() from None

    token_identifier = token_hash[:REFRESH_TOKEN_IDENTIFIER_LENGTH]
    try:
        key = check_refresh_rate_limit(token_identifier, client_ip)
    except RateLimitExceededError:
        raise RateLimitExceeded(RATE_LIMIT_MESSAGE) from None

    try:
        tokens = await _validate_and_issue_tokens(token_repo, token_hash)
    except (AuthenticationError, PermissionDenied):
        record_refresh_failure(key)
        raise
    reset_refresh_limit(key)
    return tokens
