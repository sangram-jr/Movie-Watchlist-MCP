import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class WatchlistMovie(Base):
    __tablename__ = "watchlist_movies"

    __table_args__ = (
        UniqueConstraint(
            "watchlist_id",
            "movie_id",
            name="uq_watchlist_movie",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    movie_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("movies.tmdb_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )   

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    watchlist: Mapped["Watchlist"] = relationship(
        back_populates="movies",
    )

    movie: Mapped["Movie"] = relationship(
        back_populates="watchlist_entries",
    )