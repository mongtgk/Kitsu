import uuid

from ...domain.ports.favorite import FavoriteRepository
from ...schemas.favorite import FavoriteRead


async def get_favorites(
    favorite_repo: FavoriteRepository, user_id: uuid.UUID, limit: int, offset: int
) -> list[FavoriteRead]:
    favorites = await favorite_repo.list_for_user(user_id=user_id, limit=limit, offset=offset)
    return [
        FavoriteRead(id=item.id, anime_id=item.anime_id, created_at=item.created_at)
        for item in favorites
    ]
