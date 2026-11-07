
import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_or_create_user(
    session: AsyncSession,
    supabase_user_id: str,
    email: str | None = None,
) -> User:
    """
    Find or create a Neon user using the verified Supabase identity.

    Handles concurrent requests safely using PostgreSQL
    ON CONFLICT DO NOTHING.
    """

    try:
        parsed_user_id = uuid.UUID(supabase_user_id)
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid Supabase user ID.")

    # Insert only if this Supabase identity does not exist.
    # If another request inserts it first, do nothing.
    statement = (
        insert(User)
        .values(
            supabase_user_id=parsed_user_id,
            email=None,
        )
        .on_conflict_do_nothing(
            index_elements=[User.supabase_user_id]
        )
    )

    await session.execute(statement)

    # Retrieve the existing or newly inserted user.
    result = await session.execute(
        select(User).where(
            User.supabase_user_id == parsed_user_id
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise RuntimeError(
            "Unable to retrieve authenticated user."
        )

    return user
