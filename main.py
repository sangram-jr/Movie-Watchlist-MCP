import uuid
from fastmcp import FastMCP
from app.database.connection import AsyncSessionLocal,settings
#from sqlalchemy.exc import IntegrityError
from fastmcp.server.auth.providers.supabase import SupabaseProvider
from fastmcp.server.dependencies import get_access_token
from app.services.watchlist_service import (
    create_watchlist as create_watchlist_service,
    get_watchlists as get_watchlists_service,
    add_movie_to_watchlist as add_movie_to_watchlist_service,
    get_watchlist_details as get_watchlist_details_service,
    remove_movie_from_watchlist as remove_movie_from_watchlist_service,
)
from app.services.tmdb_service import (
    search_tmdb_movies,
    get_tmdb_movie_details as fetch_tmdb_movie_details,
)
from app.services.movie_service import (
    save_movie,
)


# Supabase authentication configuration
auth = SupabaseProvider(
    project_url=settings.SUPABASE_URL,
    base_url="https://movie-watchlist-mcp.onrender.com",
    algorithm="ES256",
    scopes_supported=["openid", "profile", "email"],
    resource_name="MovieWatch MCP",
)


# Initialize MCP server
mcp = FastMCP(
    name="MovieWatch MCP",
    auth=auth,
)



def get_authenticated_user():
    """
    Extract the verified Supabase user identity
    from the current MCP request.
    """

    token = get_access_token()

    if token is None:
        raise PermissionError("Authentication required.")

    claims = token.claims

    supabase_user_id = claims.get("sub")

    if not supabase_user_id:
        raise PermissionError(
            "Supabase user ID missing from access token."
        )

    email = claims.get("email")

    return {
        "supabase_user_id": str(supabase_user_id),
        "email": email,
    }



@mcp.tool()
def hello_movie(name: str) -> str:
    """
    Welcome a user to MovieWatch MCP.
    """
    return f"Hello {name}! Welcome to MovieWatch MCP."



@mcp.tool()
async def create_watchlist(
    name: str,
    description: str | None = None,
) -> dict:
    """
    Create a new movie watchlist for the current development user.

    Args:
        name: Name of the watchlist.
        description: Optional description of the watchlist.

    Returns:
        Details of the newly created watchlist.
    """

    identity = get_authenticated_user()

    async with AsyncSessionLocal() as session:
        try:
            watchlist = await create_watchlist_service(
                session=session,
                supabase_user_id=identity["supabase_user_id"],
                email=identity["email"],
                name=name,
                description=description,
            )

            await session.commit()

            return {
                "success": True,
                "message": "Watchlist created successfully.",
                "watchlist": {
                    "id": str(watchlist.id),
                    "name": watchlist.name,
                    "description": watchlist.description,
                    #"user_id": str(watchlist.user_id),
                    "created_at": watchlist.created_at.isoformat()
                    if watchlist.created_at
                    else None,
                },
            }

        except ValueError as error:
            await session.rollback()

            return {
                "success": False,
                "error": str(error),
            }

        except Exception:
            await session.rollback()
            raise






@mcp.tool()
async def get_watchlists() -> dict:
    """
    Retrieve all watchlists belonging to the current user.

    Returns:
        A list of the user's watchlists.
    """

    identity = get_authenticated_user()

    async with AsyncSessionLocal() as session:
        try:
            watchlists = await get_watchlists_service(
                session=session,
                supabase_user_id=identity["supabase_user_id"],
                email=identity["email"],
            )

            return {
                "success": True,
                "count": len(watchlists),
                "watchlists": [
                    {
                        "id": str(watchlist.id),
                        "name": watchlist.name,
                        "description": watchlist.description,
                        "created_at": (
                            watchlist.created_at.isoformat()
                            if watchlist.created_at
                            else None
                        ),
                    }
                    for watchlist in watchlists
                ],
            }

        except Exception:
            raise





@mcp.tool()
async def add_movie_to_watchlist(
    watchlist_id: str,
    movie_id: str,
) -> dict:
    """Add a movie to a user's watchlist using its TMDB ID."""

    identity = get_authenticated_user()

    try:
        parsed_watchlist_id = uuid.UUID(watchlist_id)

        async with AsyncSessionLocal() as session:
            try:
                entry = await add_movie_to_watchlist_service(
                    session,
                    supabase_user_id=identity["supabase_user_id"],
                    watchlist_id=parsed_watchlist_id,
                    movie_id=movie_id,
                    email=identity["email"],
                )

                await session.commit()

                return {
                    "success": True,
                    "message": "Movie added to watchlist successfully.",
                    "watchlist_movie_id": str(entry.id),
                    "watchlist_id": str(entry.watchlist_id),
                    "movie_id": entry.movie_id,
                }

            except Exception:
                await session.rollback()
                raise

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }





@mcp.tool()
async def get_watchlist_details(watchlist_id: str) -> dict:
    """
    Get complete details of a watchlist,
    including all associated movie information.
    """

    identity = get_authenticated_user()

    try:
        parsed_watchlist_id = uuid.UUID(watchlist_id)

        async with AsyncSessionLocal() as session:

            watchlist = await get_watchlist_details_service(
                session=session,
                supabase_user_id=identity["supabase_user_id"],
                watchlist_id=parsed_watchlist_id,
                email=identity["email"],
            )

            if not watchlist:
                return {
                    "success": False,
                    "error": "Watchlist not found.",
                }

            # Serialize movie information while session is open
            movies = []

            for entry in watchlist.movies:
                movie = entry.movie

                if not movie:
                    continue

                movies.append({
                    "tmdb_id": movie.tmdb_id,
                    "title": movie.title,
                    "overview": movie.overview,
                    "release_date": (
                        movie.release_date.isoformat()
                        if movie.release_date else None
                    ),
                    "vote_average": movie.vote_average,
                    "poster_url": (
                        f"{settings.TMDB_IMAGE_BASE_URL}{movie.poster_path}"
                        if movie.poster_path else None
                    ),
                    "backdrop_url": (
                        f"{settings.TMDB_IMAGE_BASE_URL}{movie.backdrop_path}"
                        if movie.backdrop_path else None
                    ),
                    "added_at": (
                        entry.added_at.isoformat()
                        if entry.added_at else None
                    ),
                })

            return {
                "success": True,
                "watchlist": {
                    "id": str(watchlist.id),
                    "name": watchlist.name,
                    "description": watchlist.description,
                    "created_at": (
                        watchlist.created_at.isoformat()
                        if watchlist.created_at else None
                    ),
                    "total_movies": len(movies),
                    "movies": movies,
                },
            }

    except ValueError:
        return {
            "success": False,
            "error": "Invalid watchlist ID.",
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }






@mcp.tool()
async def search_movies(query: str, page: int = 1) -> dict:
    """
    Search movies using TMDB and save the results in our database.
    """

    try:
        # 1. Search movies from TMDB
        movies = await search_tmdb_movies(query, page)

        if not movies:
            return {
                "success": True,
                "message": "No movies found.",
                "movies": [],
            }

        saved_movies = []

        # 2. Save each movie in PostgreSQL
        async with AsyncSessionLocal() as session:
            try:
                for movie_data in movies:
                    movie = await save_movie(session, movie_data)

                    saved_movies.append({
                        "id": str(movie.id),
                        "tmdb_id": movie.tmdb_id,
                        "title": movie.title,
                        "release_date": (
                            movie.release_date.isoformat()
                            if movie.release_date else None
                        ),
                        "vote_average": movie.vote_average,
                        "poster_path": movie.poster_path,
                        "poster_url": (
                            f"{settings.TMDB_IMAGE_BASE_URL}{movie.poster_path}"
                            if movie.poster_path else None
                        ),
                    })

                await session.commit()

            except Exception:
                await session.rollback()
                raise

        # 3. Return results to the AI client
        return {
            "success": True,
            "total_results": len(saved_movies),
            "movies": saved_movies,
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }









@mcp.tool()
async def get_movie_details(tmdb_id: str) -> dict:
    """
    Fetch detailed movie information from TMDB
    and save or update it in PostgreSQL.
    """

    try:
        # 1. Fetch details from TMDB
        movie_data = await fetch_tmdb_movie_details(tmdb_id)

        # 2. Save or update movie in PostgreSQL
        async with AsyncSessionLocal() as session:
            try:
                movie = await save_movie(session, movie_data)

                await session.commit()

                return {
                    "success": True,
                    "message": "Movie details retrieved successfully.",
                    "movie": {
                        "id": str(movie.id),
                        "tmdb_id": movie.tmdb_id,
                        "title": movie.title,
                        "overview": movie.overview,
                        "release_date": (
                            movie.release_date.isoformat()
                            if movie.release_date else None
                        ),
                        "poster_path": movie.poster_path,
                        "poster_url": (
                            f"{settings.TMDB_IMAGE_BASE_URL}{movie.poster_path}"
                            if movie.poster_path else None
                        ),
                        "backdrop_path": movie.backdrop_path,
                        "vote_average": movie.vote_average,
                    },
                }

            except Exception:
                await session.rollback()
                raise

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }






@mcp.tool()
async def remove_movie_from_watchlist(
    watchlist_id: str,
    movie_id: str,
) -> dict:
    """Remove a movie from a watchlist without deleting it from the catalog."""

    identity = get_authenticated_user()

    try:
        parsed_watchlist_id = uuid.UUID(watchlist_id)

        async with AsyncSessionLocal() as session:
            try:
                removed = await remove_movie_from_watchlist_service(
                    session=session,
                    supabase_user_id=identity["supabase_user_id"],
                    watchlist_id=parsed_watchlist_id,
                    movie_id=movie_id,
                    email=identity["email"],
                )

                await session.commit()

                return {
                    "success": removed,
                    "message": "Movie removed from watchlist successfully.",
                    "movie_id": movie_id,
                }

            except Exception:
                await session.rollback()
                raise

    except ValueError as error:
        return {
            "success": False,
            "error": str(error),
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }





if __name__ == "__main__":
    mcp.run()

