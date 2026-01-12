from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.refresh_token import get_refresh_token_by_hash
from ...errors import AppError, AuthError, PermissionError
from ...utils.security import hash_refresh_token
from .register_user import AuthTokens, issue_tokens


async def refresh_session(session: AsyncSession, refresh_token: str) -> AuthTokens:
    token_hash = hash_refresh_token(refresh_token)
    try:
        stored_token = await get_refresh_token_by_hash(
            session, token_hash, for_update=True
        )
        if stored_token is None:
            raise AuthError()
        if stored_token.revoked:
            raise PermissionError()
        if stored_token.expires_at <= datetime.now(timezone.utc):
            raise AuthError()

        return await issue_tokens(session, stored_token.user_id)
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
