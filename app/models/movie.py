import uuid
from datetime import date, datetime

from sqlalchemy import (
    String,
    Text,
    Date,
    DateTime,
    Float,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    provider: Mapped[str] = mapped_column(
        String(30),
        default="tmdb",
        nullable=False,
    )

    tmdb_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    overview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    release_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    poster_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    backdrop_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    vote_average: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    watchlist_entries: Mapped[list["WatchlistMovie"]] = relationship(
        back_populates="movie",
    )