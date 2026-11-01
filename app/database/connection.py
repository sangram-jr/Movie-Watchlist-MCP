
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from sqlalchemy import text
from pydantic_settings import BaseSettings, SettingsConfigDict


# Load environment variables
class Settings(BaseSettings):
    DATABASE_URL: str
    DEV_USER_EMAIL: str = "developer@example.com"

    TMDB_API_KEY: str
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w500"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


# Create asynchronous database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Test database connection
async def test_db_connection():

    try:
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

    finally:
        await engine.dispose()
