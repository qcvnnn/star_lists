from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.session import get_db
from models import User


redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    session_id = request.cookies.get(
        settings.SESSION_COOKIE_NAME
    )

    if session_id is None:
        return None

    user_id = await redis_client.get(
        f"session:{session_id}"
    )

    if user_id is None:
        return None

    user = await db.get(User, int(user_id))

    if user is None:
        return None

    return {"id": user.id}


async def get_current_user(
    current_user: dict | None = Depends(get_optional_user),
):
    if current_user is None:
        raise HTTPException(status_code=401)

    return current_user
