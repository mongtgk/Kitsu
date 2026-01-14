from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid

from ...config import settings
from ...domain.ports.token import TokenRepository
from ...domain.ports.user import UserRepository
from ...errors import ValidationError
from ...utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
)


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: str


async def issue_tokens(token_repo: TokenRepository, user_id: uuid.UUID) -> AuthTokens:
    access_token = create_access_token({"sub": str(user_id)})
    refresh_token = create_refresh_token()
    token_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    await token_repo.save_or_rotate(user_id, token_hash, expires_at)
    return AuthTokens(access_token=access_token, refresh_token=refresh_token)


async def register_user(
    user_repo: UserRepository, token_repo: TokenRepository, email: str, password: str
) -> AuthTokens:
    existing_user = await user_repo.get_by_email(email)
    if existing_user:
        raise ValidationError("Email already registered")

    user = await user_repo.add(email=email, password_hash=hash_password(password))
    return await issue_tokens(token_repo, user.id)
