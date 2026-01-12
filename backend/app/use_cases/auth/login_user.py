from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.user import get_user_by_email
from ...errors import AppError, AuthError
from ...utils.security import verify_password
from .register_user import AuthTokens, issue_tokens


async def login_user(
    session: AsyncSession, email: str, password: str
) -> AuthTokens:
    try:
        user = await get_user_by_email(session, email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError()

        return await issue_tokens(session, user.id)
    except AppError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
