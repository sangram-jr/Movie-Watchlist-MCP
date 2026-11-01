import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie,Watchlist,WatchlistMovie
from app.services.dev_identity import get_or_create_dev_user
from sqlalchemy import select
from sqlalchemy.orm import selectinload


# create watchlist for particular user
async def create_watchlist(
    session: AsyncSession,
    name: str,
    description: str | None = None,
) -> Watchlist:
    """
    Create a watchlist for the current development user.
    """

    # Validate watchlist name
    name = name.strip()

    if not name:
        raise ValueError("Watchlist name cannot be empty.")

    if len(name) > 100:
        raise ValueError("Watchlist name cannot exceed 100 characters.")

    if description is not None:
        description = description.strip() or None

    # Get the development user
    user = await get_or_create_dev_user(session)

    # Create watchlist
    watchlist = Watchlist(
        user_id=user.id,
        name=name,
        description=description,
    )

    session.add(watchlist)

    await session.flush()

    return watchlist



# get all the watchlist based on userid
async def get_watchlists(
    session: AsyncSession,
) -> list[Watchlist]:
    """
    Retrieve all watchlists belonging to the current development user.
    """

    # Get current development user
    user = await get_or_create_dev_user(session)

    # Fetch only this user's watchlists
    result = await session.execute(
        select(Watchlist)
        .where(Watchlist.user_id == user.id)
        .order_by(Watchlist.created_at.desc())
    )

    watchlists = result.scalars().all()

    return list(watchlists)








# add movie to the particular watchlist

async def add_movie_to_watchlist(
    session: AsyncSession,
    watchlist_id: uuid.UUID,
    movie_id: str,
) -> WatchlistMovie:
    """
    Add an existing movie from the movies catalog
    to a user's watchlist.

    movie_id represents the TMDB movie ID.
    """

    movie_id = str(movie_id).strip()

    if not movie_id or len(movie_id) > 100:
        raise ValueError("Invalid movie ID.")

    # 1. Get the current development user
    user = await get_or_create_dev_user(session)

    # 2. Verify that the watchlist belongs to this user
    result = await session.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id,
        )
    )

    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise ValueError("Watchlist not found.")

    # 3. Verify that the movie exists in our movie catalog
    result = await session.execute(
        select(Movie).where(Movie.tmdb_id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if not movie:
        raise ValueError(
            "Movie not found in database. "
            "Search for the movie first using search_movies."
        )

    # 4. Check whether the movie is already in this watchlist
    result = await session.execute(
        select(WatchlistMovie).where(
            WatchlistMovie.watchlist_id == watchlist.id,
            WatchlistMovie.movie_id == movie.tmdb_id,
        )
    )

    existing_entry = result.scalar_one_or_none()

    if existing_entry:
        raise ValueError("Movie already exists in this watchlist.")

    # 5. Create watchlist entry
    watchlist_movie = WatchlistMovie(
        watchlist_id=watchlist.id,
        movie_id=movie.tmdb_id,
    )

    session.add(watchlist_movie)

    await session.flush()

    return watchlist_movie







async def get_watchlist_details(
    session: AsyncSession,
    watchlist_id: uuid.UUID,
) -> Watchlist | None:
    """
    Get a watchlist with its complete movie information.
    """

    # 1. Get the current development user
    user = await get_or_create_dev_user(session)

    # 2. Fetch watchlist, movie entries and related movies
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







async def remove_movie_from_watchlist(
    session: AsyncSession,
    watchlist_id: uuid.UUID,
    movie_id: str,
) -> bool:
    """
    Remove a movie from a user's watchlist.
    The movie remains in the movies catalog.
    """

    movie_id = str(movie_id).strip()

    if not movie_id or len(movie_id) > 100:
        raise ValueError("Invalid movie ID.")

    # 1. Get current development user
    user = await get_or_create_dev_user(session)

    # 2. Verify watchlist ownership
    result = await session.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id,
        )
    )

    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise ValueError("Watchlist not found.")

    # 3. Find movie entry in this watchlist
    result = await session.execute(
        select(WatchlistMovie).where(
            WatchlistMovie.watchlist_id == watchlist.id,
            WatchlistMovie.movie_id == movie_id,
        )
    )

    entry = result.scalar_one_or_none()

    if not entry:
        raise ValueError("Movie not found in this watchlist.")

    # 4. Delete only the watchlist entry
    await session.delete(entry)
    await session.flush()

    return True
