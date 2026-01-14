import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ..domain.entities import Anime as DomainAnime
from ..domain.entities import Favorite as DomainFavorite
from ..domain.entities import RefreshToken as DomainRefreshToken
from ..domain.entities import User as DomainUser
from ..domain.entities import WatchProgress as DomainWatchProgress
from ..domain.ports.anime import AnimeRepository
from ..domain.ports.favorite import FavoriteRepository
from ..domain.ports.token import TokenRepository
from ..domain.ports.user import UserRepository
from ..domain.ports.watch_progress import WatchProgressRepository
from ..models.user import User
from . import anime as anime_crud
from . import favorite as favorite_crud
from . import refresh_token as token_crud
from . import user as user_crud
from . import watch_progress as watch_crud


def _to_domain_user(model: Any | None) -> DomainUser | None:
    if model is None:
        return None
    return DomainUser(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        is_active=model.is_active,
        created_at=model.created_at,
    )


def _to_domain_refresh_token(model: Any | None) -> DomainRefreshToken | None:
    if model is None:
        return None
    return DomainRefreshToken(
        user_id=model.user_id,
        token_hash=model.token_hash,
        expires_at=model.expires_at,
        revoked=model.revoked,
    )


def _to_domain_anime(model: Any | None) -> DomainAnime | None:
    if model is None:
        return None
    return DomainAnime(id=model.id)


def _to_domain_favorite(model: Any | None) -> DomainFavorite | None:
    if model is None:
        return None
    return DomainFavorite(
        id=model.id,
        user_id=model.user_id,
        anime_id=model.anime_id,
        created_at=model.created_at,
    )


def _to_domain_watch_progress(model: Any | None) -> DomainWatchProgress | None:
    if model is None:
        return None
    return DomainWatchProgress(
        id=model.id,
        user_id=model.user_id,
        anime_id=model.anime_id,
        episode=model.episode,
        position_seconds=model.position_seconds,
        progress_percent=model.progress_percent,
        created_at=model.created_at,
        last_watched_at=model.last_watched_at,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> DomainUser | None:
        user = await user_crud.get_user_by_email(self.session, email)
        return _to_domain_user(user)

    async def add(self, email: str, password_hash: str) -> DomainUser:
        user = User(email=email, password_hash=password_hash)
        try:
            self.session.add(user)
            await self.session.flush()
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise
        domain_user = _to_domain_user(user)
        assert domain_user is not None
        return domain_user


class SqlAlchemyTokenRepository(TokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_or_rotate(
        self, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> DomainRefreshToken:
        try:
            token = await token_crud.create_or_rotate_refresh_token(
                self.session, user_id, token_hash, expires_at
            )
            await self.session.commit()
            domain_token = _to_domain_refresh_token(token)
            assert domain_token is not None
            return domain_token
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_hash(
        self, token_hash: str, *, for_update: bool = False
    ) -> DomainRefreshToken | None:
        token = await token_crud.get_refresh_token_by_hash(
            self.session, token_hash, for_update=for_update
        )
        return _to_domain_refresh_token(token)

    async def revoke_for_user(self, user_id: uuid.UUID) -> None:
        try:
            await token_crud.revoke_refresh_token(self.session, user_id)
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise


class SqlAlchemyAnimeRepository(AnimeRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, anime_id: uuid.UUID) -> DomainAnime | None:
        anime = await anime_crud.get_anime_by_id(self.session, anime_id)
        return _to_domain_anime(anime)


class SqlAlchemyFavoriteRepository(FavoriteRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: uuid.UUID, anime_id: uuid.UUID) -> DomainFavorite | None:
        favorite = await favorite_crud.get_favorite(self.session, user_id, anime_id)
        return _to_domain_favorite(favorite)

    async def add(
        self,
        user_id: uuid.UUID,
        anime_id: uuid.UUID,
        *,
        favorite_id: uuid.UUID | None = None,
        created_at: datetime | None = None,
    ) -> DomainFavorite:
        try:
            favorite = await favorite_crud.add_favorite(
                self.session,
                user_id,
                anime_id,
                favorite_id=favorite_id,
                created_at=created_at,
            )
            await self.session.commit()
            domain_favorite = _to_domain_favorite(favorite)
            assert domain_favorite is not None
            return domain_favorite
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def remove(self, user_id: uuid.UUID, anime_id: uuid.UUID) -> bool:
        try:
            deleted = await favorite_crud.remove_favorite(self.session, user_id, anime_id)
            await self.session.commit()
            return deleted
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def list_for_user(
        self, user_id: uuid.UUID, limit: int, offset: int
    ) -> list[DomainFavorite]:
        favorites = await favorite_crud.list_favorites(self.session, user_id, limit, offset)
        result: list[DomainFavorite] = []
        for favorite in favorites:
            domain_favorite = _to_domain_favorite(favorite)
            if domain_favorite is not None:
                result.append(domain_favorite)
        return result


class SqlAlchemyWatchProgressRepository(WatchProgressRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: uuid.UUID, anime_id: uuid.UUID) -> DomainWatchProgress | None:
        progress = await watch_crud.get_watch_progress(self.session, user_id, anime_id)
        return _to_domain_watch_progress(progress)

    async def list_for_user(self, user_id: uuid.UUID, limit: int) -> list[DomainWatchProgress]:
        progress_list = await watch_crud.list_watch_progress(self.session, user_id, limit)
        result: list[DomainWatchProgress] = []
        for progress_item in progress_list:
            domain_progress = _to_domain_watch_progress(progress_item)
            if domain_progress is not None:
                result.append(domain_progress)
        return result

    async def upsert(
        self,
        user_id: uuid.UUID,
        anime_id: uuid.UUID,
        episode: int,
        position_seconds: int | None,
        progress_percent: float | None,
        *,
        progress_id: uuid.UUID,
        created_at: datetime,
        last_watched_at: datetime,
    ) -> DomainWatchProgress:
        result = None
        try:
            existing = await watch_crud.get_watch_progress(self.session, user_id, anime_id)
            if existing:
                result = await watch_crud.update_watch_progress(
                    self.session,
                    existing,
                    episode,
                    position_seconds,
                    progress_percent,
                    last_watched_at=last_watched_at,
                )
            else:
                result = await watch_crud.create_watch_progress(
                    self.session,
                    user_id,
                    anime_id,
                    episode,
                    position_seconds,
                    progress_percent,
                    progress_id=progress_id,
                    created_at=created_at,
                    last_watched_at=last_watched_at,
                )
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        domain_progress = _to_domain_watch_progress(result)
        assert domain_progress is not None
        return domain_progress
