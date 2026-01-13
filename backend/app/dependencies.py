import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import rbac
from .database import get_session
from .models.user import User
from .utils.security import (
    TokenExpiredError,
    TokenInvalidError,
    decode_access_token,
)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        ) from None
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from None

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    try:
        if not isinstance(subject, str):
            raise ValueError("invalid-subject-type")
        user_id = uuid.UUID(subject)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        ) from None

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


async def _get_user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except (TokenExpiredError, TokenInvalidError):
        return None

    subject = payload.get("sub")
    if subject is None or not isinstance(subject, str):
        return None

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        return None

    return await db.get(User, user_id)


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    return await _get_user_from_credentials(credentials, db)


async def get_current_role(
    user: User | None = Depends(get_current_principal),
) -> rbac.Role:
    return rbac.resolve_role(user)


async def get_current_permissions(
    role: rbac.Role = Depends(get_current_role),
) -> list[rbac.Permission]:
    return rbac.resolve_permissions(role)
