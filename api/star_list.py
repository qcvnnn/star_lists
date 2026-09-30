from datetime import date, datetime, timezone
from fastapi import APIRouter, Query, HTTPException, Depends, Form, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from core.config import settings
from models import Star, Like, User
from data.media import media_url

from fastapi import File, UploadFile
from starlette.concurrency import run_in_threadpool
from pathlib import Path
from uuid import uuid4
from minio import Minio
from schemas.api import RegisterRequest, UserRead, StarRead, StarDetailRead, PublishRequest, LikeRequest
from core.current_user import get_current_user


router = APIRouter(prefix="/api/star_list")
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)

def upload_file(file) -> str:
    extension = Path(file.filename or "").suffix.lower()
    object_name = f"{uuid4().hex}{extension}"

    minio_client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=object_name,
        data=file.file,
        length=-1,
        part_size=10 * 1024 * 1024,
        content_type=file.content_type or "application/octet-stream",
    )

    return object_name



@router.get("/draft", response_model=StarDetailRead)
async def open_draft(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user),):
    star = await db.scalar(
        select(Star).where(
            Star.status == "Черновик",
            Star.creator_id == current_user["id"]
        )
    )
    if star is None:
        return Response(status_code=404)

    likes_count = await db.scalar(
            select(func.count(Like.id)).where(Like.star_id == star.id)
        )

    return {
        "id": star.id,
        "creator_id": star.creator_id,
        "title": star.title,
        "image_url": media_url(star.image_url, "image"),
        "video_url": media_url(star.video_url, "video"),
        "received_date": star.received_date,
        "habitable_planets": star.habitable_planets,
        "likes_count": likes_count,
        "is_owner": int(star.creator_id == current_user["id"]),
        "description": star.description,
    }


@router.post("/stars")
async def create_star(
    title: str = Form(..., min_length=1, max_length=100),
    image: UploadFile = File(...),
    video: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = await db.scalar(
        select(User)
        .where(User.id == current_user["id"])
        .with_for_update()
    )
    if user is None:
        return Response(status_code=404)

    draft = await db.scalar(
        select(Star).where(
            Star.creator_id == current_user["id"],
            Star.status == "Черновик",
        )
    )
    if draft is not None:
        return Response(status_code=404)
    image_name = await run_in_threadpool(upload_file, image)
    video_name = await run_in_threadpool(upload_file, video)
    star = Star(
        title=title,
        image_url=image_name,
        video_url=video_name,
        status="Черновик",
        creator_id=current_user["id"],
    )
    db.add(star)
    await db.commit()
    return Response(status_code=202)

@router.put("/stars/{star_id}/publish")
async def publish_star(
    star_id: int,
    payload: PublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):


    star = await db.scalar(
        select(Star).where(
            Star.id == star_id,
            Star.creator_id == current_user["id"],
            Star.status == "Черновик",
        ).with_for_update()
    )
    if star is None:
        return Response(status_code=404)

    star.description = payload.description
    star.received_date = payload.received_date
    star.habitable_planets = payload.habitable_planets
    star.status = "Опубликован"
    star.formed_at = datetime.now(timezone.utc)
    await db.commit()
    return Response(status_code=200)


@router.delete("/stars/{star_id}")
async def delete_star(star_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),):
    star = await db.scalar(
        select(Star).where(
            Star.id == star_id,
            Star.creator_id == current_user["id"],
            Star.status != "Удален",
        )
    )

    if star is None:
        return Response(status_code=404)

    star.status = "Удален"
    await db.commit()

    return Response(status_code=200)

@router.post("/stars/{star_id}/likes")
async def set_like(
    star_id: int,
    payload: LikeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = await db.scalar(
        select(User)
        .where(User.id == current_user["id"])
        .with_for_update()
    )

    if user is None:
        return Response(status_code=404)

    star = await db.scalar(
        select(Star).where(
            Star.id == star_id,
            Star.status == "Опубликован",
        ).with_for_update()
    )

    if star is None:
        return Response(status_code=404)

    like = await db.scalar(
        select(Like).where(
            Like.user_id == current_user["id"],
            Like.star_id == star_id,
        )
    )

    if payload.value == 1 and like is None:
        db.add(
            Like(
                user_id=current_user["id"],
                star_id=star_id,
            )
        )
    elif payload.value == 0 and like is not None:
        await db.delete(like)

    await db.commit()

    return Response(status_code=200)


@router.get("/feed", response_model=StarDetailRead)
async def get_star_detail(
    db: AsyncSession = Depends(get_db),
    star_id: int | None = Query(default=None, alias="id"),
    next_star: bool = Query(default=False, alias="next"),
    current_user: dict = Depends(get_current_user),
):
    published = select(Star).where(Star.status == "Опубликован")

    if star_id is None:
        star = await db.scalar(published.order_by(Star.id).limit(1))
    else:
        star = await db.scalar(published.where(Star.id == star_id))

    if star is None:
        return Response(status_code=404)

    if next_star:
        following = await db.scalar(
            published.where(Star.id > star.id).order_by(Star.id).limit(1)
        )
        star = following if following is not None else await db.scalar(
            published.order_by(Star.id).limit(1)
        )
        if star is None:
            return Response(status_code=404)

    likes_count = await db.scalar(
        select(func.count(Like.id)).where(Like.star_id == star.id)
    )

    return {
        "id": star.id,
        "creator_id": star.creator_id,
        "title": star.title,
        "image_url": media_url(star.image_url, "image"),
        "video_url": media_url(star.video_url, "video"),
        "received_date": star.received_date,
        "habitable_planets": star.habitable_planets,
        "likes_count": likes_count,
        "is_owner": int(star.creator_id == current_user["id"]),
        "description": star.description,
    }


@router.get("/catalog", response_model=list[StarRead])
async def get_catalog_star(
    received_date: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    filter_date = None
    if received_date:
        try:
            filter_date = date.fromisoformat(received_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Дата должна быть в формате ГГГГ-ММ-ДД")

    query = (
        select(Star, func.count(Like.id).label("likes_count"))
        .outerjoin(Like, Like.star_id == Star.id)
        .where(Star.status == "Опубликован")
        .group_by(Star.id)
        .order_by(Star.id)
    )

    if filter_date is not None:
        query = query.where(Star.received_date == filter_date)

    stars = []
    for star, likes_count in await db.execute(query):
        stars.append({
            "id": star.id,
            "creator_id": star.creator_id,
            "title": star.title,
            "image_url": media_url(star.image_url, "image"),
            "video_url": media_url(star.video_url, "video"),
            "received_date": star.received_date,
            "habitable_planets": star.habitable_planets,
            "likes_count": likes_count,
            "is_owner": int(star.creator_id == current_user["id"]),
        })

    return stars




@router.post("/users", response_model=UserRead, status_code=201)
async def register_user(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = User(
    username=payload.username,
    password=payload.password,
)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserRead(
        id=user.id,
        username=user.username
    )

@router.post("/users/login")
async def login_user():
    return Response(status_code=200)

@router.post("/users/logout")
async def logout_user():
    return Response(status_code=200)
