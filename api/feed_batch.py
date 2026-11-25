from uuid import UUID, uuid4

from fastapi import Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.current_user import redis_client
from models import Star


async def feed_batch(
    request: Request,
    response: Response,
    db: AsyncSession,
    user_id: int | None,
    after_id: int | None,
) -> list[int]:
    session = getattr(request.state, "feed_session", request.cookies.get("feed_session", ""))
    try:
        session = UUID(session).hex
    except ValueError:
        session = uuid4().hex
    request.state.feed_session = session
    owner = f"user:{user_id}" if user_id is not None else "guest"
    key = f"feed:{owner}:{session}"
    ttl = 3600
    response.set_cookie("feed_session", session, max_age=ttl, httponly=True)

    async with redis_client.lock(f"{key}:lock", timeout=30, blocking_timeout=5):
        ids = [int(value) for value in await redis_client.lrange(key, 0, -1)]
        if not ids or (after_id is not None and after_id == ids[-1]):
            query = select(Star.id).where(Star.status == "Опубликован")
            if ids:
                query = query.order_by(Star.id.in_(ids))
            fresh = list(await db.scalars(query.order_by(func.random()).limit(100)))
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.delete(key)
                if fresh:
                    pipe.rpush(key, *fresh)
                    pipe.expire(key, ttl)
                await pipe.execute()
            return fresh

        await redis_client.expire(key, ttl)
        if after_id in ids:
            return ids[ids.index(after_id) + 1:]
        return ids
