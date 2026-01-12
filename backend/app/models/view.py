from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from .base import Base


class View(Base):
    __tablename__ = "views"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    progress = Column(Integer, nullable=False, default=0)
    last_viewed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    device = Column(String(128))

