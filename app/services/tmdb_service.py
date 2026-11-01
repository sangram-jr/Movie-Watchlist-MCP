
import httpx

from app.database.connection import settings


async def search_tmdb_movies(query: str, page: int = 1) -> list[dict]:
    """
    Search movies using the TMDB API.
    """

    query = query.strip()

    if not query:
        raise ValueError("Movie search query cannot be empty.")

    if page < 1:
        raise ValueError("Page must be greater than or equal to 1.")

    url = f"{settings.TMDB_BASE_URL}/search/movie"

    headers = {
        "Authorization": f"Bearer {settings.TMDB_API_KEY}",
        "accept": "application/json",
    }

    params = {
        "query": query,
        "page": page,
        "include_adult": False,
        "language": "en-US",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            url,
            headers=headers,
            params=params,
        )
        response.raise_for_status()

        data = response.json()

    movies = []

    for item in data.get("results", []):
        movies.append({
            "tmdb_id": str(item["id"]),
            "title": item.get("title"),
            "overview": item.get("overview"),
            "release_date": item.get("release_date") or None,
            "poster_path": item.get("poster_path"),
            "backdrop_path": item.get("backdrop_path"),
            "vote_average": item.get("vote_average"),
        })

    return movies


async def get_tmdb_movie_details(tmdb_id: str) -> dict:
    """
    Fetch complete movie details using its TMDB ID.
    """

    tmdb_id = str(tmdb_id).strip()

    if not tmdb_id.isdigit():
        raise ValueError("TMDB movie ID must contain only digits.")

    url = f"{settings.TMDB_BASE_URL}/movie/{tmdb_id}"

    headers = {
        "Authorization": f"Bearer {settings.TMDB_API_KEY}",
        "accept": "application/json",
    }

    params = {
        "language": "en-US",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            url,
            headers=headers,
            params=params,
        )
        response.raise_for_status()

        data = response.json()

    return {
        "tmdb_id": str(data["id"]),
        "title": data.get("title"),
        "overview": data.get("overview"),
        "release_date": data.get("release_date") or None,
        "poster_path": data.get("poster_path"),
        "backdrop_path": data.get("backdrop_path"),
        "vote_average": data.get("vote_average"),
    }
