from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import settings
from app.models import User


async def get_or_create_dev_user(session: AsyncSession) -> User:
    """
    Get the temporary development user.
    Create the user if it does not exist.
    """

    result = await session.execute(
        select(User).where(
            User.email == settings.DEV_USER_EMAIL
        )
    )

    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(
        email=settings.DEV_USER_EMAIL
    )

    session.add(user)

    await session.flush()

    return user