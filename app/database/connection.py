
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import text
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # These values are supplied at runtime.
    # They are optional during FastMCP's build-time inspection.
    DATABASE_URL: str | None = None
    TMDB_API_KEY: str | None = None

    DEV_USER_EMAIL: str = "developer@example.com"
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w500"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


# Create the engine only when the application needs the database.
_engine = None
_session_factory = None


def get_engine():
    global _engine

    if _engine is None:
        if not settings.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is missing. Configure it in the "
                "deployment environment variables."
            )

        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )

    return _engine


def get_session_factory():
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _session_factory


# Keeps existing usage compatible:
# async with AsyncSessionLocal() as session:
class LazySessionLocal:

    def __call__(self):
        return get_session_factory()()


AsyncSessionLocal = LazySessionLocal()


def get_tmdb_api_key() -> str:
    if not settings.TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is missing. Configure it in the "
            "deployment environment variables."
        )

    return settings.TMDB_API_KEY


async def test_db_connection():

    try:
        engine = get_engine()

        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT version()")
            )

            version = result.scalar_one()

            print("Database connected successfully!")
            print("PostgreSQL version:", version)

    except Exception as e:
        print("Database connection failed:", str(e))
        raise
