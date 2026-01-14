from ...domain.ports.token import TokenRepository
from ...utils.security import hash_refresh_token


async def logout_user(token_repo: TokenRepository, refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)
    stored_token = await token_repo.get_by_hash(token_hash, for_update=True)
    if stored_token is None:
        return
    await token_repo.revoke_for_user(stored_token.user_id)
