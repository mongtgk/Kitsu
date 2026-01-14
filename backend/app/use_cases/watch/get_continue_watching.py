import uuid

from ...domain.ports.watch_progress import WatchProgressRepository
from ...schemas.watch import WatchProgressRead


async def get_continue_watching(
    repo: WatchProgressRepository, user_id: uuid.UUID, limit: int
) -> list[WatchProgressRead]:
    progress_list = await repo.list_for_user(user_id=user_id, limit=limit)
    return [
        WatchProgressRead(
            id=item.id,
            anime_id=item.anime_id,
            episode=item.episode,
            position_seconds=item.position_seconds,
            progress_percent=item.progress_percent,
            created_at=item.created_at,
            last_watched_at=item.last_watched_at,
        )
        for item in progress_list
    ]
