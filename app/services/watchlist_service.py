

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Movie, Watchlist, WatchlistMovie
from app.services.user_service import get_or_create_user


# 1. Create a watchlist
async def create_watchlist(
    session: AsyncSession,
    supabase_user_id: str,
    name: str,
    description: str | None = None,
    email: str | None = None,
) -> Watchlist:
    """Create a watchlist for the authenticated Supabase user."""

    name = name.strip()

    if not name:
        raise ValueError("Watchlist name cannot be empty.")

    if len(name) > 100:
        raise ValueError("Watchlist name cannot exceed 100 characters.")

    if description is not None:
        description = description.strip() or None

    user = await get_or_create_user(
        session=session,
        supabase_user_id=supabase_user_id,
        email=email,
    )

    watchlist = Watchlist(
        user_id=user.id,
        name=name,
        description=description,
    )

    session.add(watchlist)
    await session.flush()

    return watchlist


# 2. Get all watchlists for the authenticated user
async def get_watchlists(
    session: AsyncSession,
    supabase_user_id: str,
    email: str | None = None,
) -> list[Watchlist]:
    """Retrieve only the authenticated user's watchlists."""

    user = await get_or_create_user(
        session=session,
        supabase_user_id=supabase_user_id,
        email=email,
    )

    result = await session.execute(
        select(Watchlist)
        .where(Watchlist.user_id == user.id)
        .order_by(Watchlist.created_at.desc())
    )

    return list(result.scalars().all())


# 3. Add a movie to a watchlist
async def add_movie_to_watchlist(
    session: AsyncSession,
    supabase_user_id: str,
    watchlist_id: uuid.UUID,
    movie_id: str,
    email: str | None = None,
) -> WatchlistMovie:
    """Add an existing movie to the authenticated user's watchlist."""

    movie_id = str(movie_id).strip()

    if not movie_id or len(movie_id) > 100:
        raise ValueError("Invalid movie ID.")

    user = await get_or_create_user(
        session=session,
        supabase_user_id=supabase_user_id,
        email=email,
    )

    # Verify ownership
    result = await session.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id,
        )
    )

    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise ValueError("Watchlist not found.")

    # Verify movie exists
    result = await session.execute(
        select(Movie).where(Movie.tmdb_id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if not movie:
        raise ValueError(
            "Movie not found in database. "
            "Search for the movie first using search_movies."
        )

    # Prevent duplicate entries
    result = await session.execute(
        select(WatchlistMovie).where(
            WatchlistMovie.watchlist_id == watchlist.id,
            WatchlistMovie.movie_id == movie.tmdb_id,
        )
    )

    if result.scalar_one_or_none():
        raise ValueError("Movie already exists in this watchlist.")

    watchlist_movie = WatchlistMovie(
        watchlist_id=watchlist.id,
        movie_id=movie.tmdb_id,
    )

    session.add(watchlist_movie)
    await session.flush()

    return watchlist_movie


# 4. Get watchlist details
async def get_watchlist_details(
    session: AsyncSession,
    supabase_user_id: str,
    watchlist_id: uuid.UUID,
    email: str | None = None,
) -> Watchlist | None:
    """Get a watchlist only if it belongs to the authenticated user."""

    user = await get_or_create_user(
        session=session,
        supabase_user_id=supabase_user_id,
        email=email,
    )

    result = await session.execute(
        select(Watchlist)
        .where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id,
        )
        .options(
            selectinload(Watchlist.movies).selectinload(
                WatchlistMovie.movie
            )
        )
    )

    return result.scalar_one_or_none()


# 5. Remove a movie from a watchlist
async def remove_movie_from_watchlist(
    session: AsyncSession,
    supabase_user_id: str,
    watchlist_id: uuid.UUID,
    movie_id: str,
    email: str | None = None,
) -> bool:
    """Remove a movie only from the authenticated user's watchlist."""

    movie_id = str(movie_id).strip()

    if not movie_id or len(movie_id) > 100:
        raise ValueError("Invalid movie ID.")

    user = await get_or_create_user(
        session=session,
        supabase_user_id=supabase_user_id,
        email=email,
    )

    # Verify ownership
    result = await session.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id,
        )
    )

    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise ValueError("Watchlist not found.")

    # Find the movie entry
    result = await session.execute(
        select(WatchlistMovie).where(
            WatchlistMovie.watchlist_id == watchlist.id,
            WatchlistMovie.movie_id == movie_id,
        )
    )

    entry = result.scalar_one_or_none()

    if not entry:
        raise ValueError("Movie not found in this watchlist.")

    await session.delete(entry)
    await session.flush()

    return True

