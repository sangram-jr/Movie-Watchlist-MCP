
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Movie


async def save_movie(
    session: AsyncSession,
    movie_data: dict,
) -> Movie:
    """
    Save a movie in the database.
    If it already exists, update its metadata.
    """

    tmdb_id = str(movie_data["tmdb_id"])

    result = await session.execute(
        select(Movie).where(Movie.tmdb_id == tmdb_id)
    )

    movie = result.scalar_one_or_none()

    release_date = movie_data.get("release_date")

    if release_date:
        release_date = date.fromisoformat(release_date)

    movie_fields = {
        "title": movie_data["title"],
        "overview": movie_data.get("overview"),
        "release_date": release_date,
        "poster_path": movie_data.get("poster_path"),
        "backdrop_path": movie_data.get("backdrop_path"),
        "vote_average": movie_data.get("vote_average"),
    }

    if movie:
        # Update existing movie
        for key, value in movie_fields.items():
            setattr(movie, key, value)
    else:
        # Insert new movie
        movie = Movie(
            tmdb_id=tmdb_id,
            provider="tmdb",
            **movie_fields,
        )
        session.add(movie)

    await session.flush()

    return movie


async def get_movie_by_tmdb_id(
    session: AsyncSession,
    tmdb_id: str,
) -> Movie | None:
    """
    Retrieve a movie from our database using its TMDB ID.
    """

    result = await session.execute(
        select(Movie).where(Movie.tmdb_id == str(tmdb_id))
    )

    return result.scalar_one_or_none()
