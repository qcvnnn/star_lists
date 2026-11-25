from api.feed_batch import feed_batch
from datetime import date, datetime, timezone
from fastapi import APIRouter, Query, HTTPException, Depends, Form, Response, Request
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
from schemas.api import CatalogRead, FeedRead, NativeStarRead, RegisterRequest, UserRead, StarDetailRead, PublishRequest, LikeRequest, LoginRequest
from core.current_user import (
    get_current_user,
    get_optional_user,
    redis_client,
)

from secrets import token_urlsafe
from core.config import ROOT_DIR


router = APIRouter(prefix="/api/star_list")
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)

CREATE_SESSION_SCRIPT = (
    ROOT_DIR / "scripts" / "create_session.lua"
).read_text(encoding="utf-8")

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



@router.get("/draft", response_model=StarDetailRead,
    summary='Получить свой черновик',
    description='Требуется вход. Единственный черновик текущего пользователя; ID не передаётся.',
    tags=['Звёзды'],
    responses={401: {'description': ''}, 404: {'description': ''}},
)
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


@router.post("/stars", response_class=Response, status_code=202,
    summary='Создать звезду',
    description='Требуется вход. Название и два файла передаются как multipart/form-data. Файлы сохраняются в MinIO. Создатель определяется по сессии. Не более одного черновика.',
    tags=['Звёзды'],
    responses={401: {'description': ''}, 404: {'description': ''}},
)
async def create_star(
    title: str = Form(..., min_length=1, max_length=100),
    image: UploadFile = File(..., description="Файл изображения"),
    video: UploadFile = File(..., description="Файл видео"),
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

@router.put("/stars/{star_id}/publish", response_class=Response,
    summary='Опубликовать звезду',
    description='Требуется вход. Заполняет поля и публикует только собственный черновик. Дата формирования устанавливается сервером.',
    tags=['Звёзды'],
    responses={401: {'description': ''}, 404: {'description': ''}},
)
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


@router.delete("/stars/{star_id}", response_class=Response,
    summary='Удалить свою звезду',
    description='Требуется вход. Логическое удаление собственной звезды; запись остаётся в БД.',
    tags=['Звёзды'],
    responses={401: {'description': ''}, 404: {'description': ''}},
)
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

@router.post("/stars/{star_id}/likes", response_class=Response,
    summary='Поставить или снять лайк',
    description='Требуется вход. value=1 ставит лайк, value=0 снимает. Только опубликованные звёзды. Повторный лайк не создаёт дубликат.',
    tags=['Звёзды'],
    responses={401: {'description': ''}, 404: {'description': ''}},
)
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


@router.get("/feed", response_model=FeedRead,
    summary='Получить ленту',
    description='Доступно гостю. Без id — первая карточка из случайной подборки в Redis. next=true — следующая карточка; после последней формируется новая подборка.',
    tags=['Звёзды'],
    responses={},
)
async def get_star_detail(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    star_id: int | None = Query(default=None, alias="id", description="ID опубликованной звезды; без ID — первая"),
    next_star: bool = Query(default=False, alias="next", description="Открыть следующую опубликованную звезду"),
    current_user: dict | None = Depends(get_optional_user),
):
    published = select(Star).where(Star.status == "Опубликован")
    if star_id is None or next_star:
        ids = await feed_batch(
            request, response, db,
            current_user["id"] if current_user else None,
            star_id if next_star else None,
        )
        available = {star.id: star for star in await db.scalars(
            published.where(Star.id.in_(ids))
        )}
        star = next((available[id_] for id_ in ids if id_ in available), None)
        if star is None and ids:
            ids = await feed_batch(request, response, db, current_user["id"] if current_user else None, ids[-1])
            available = {star.id: star for star in await db.scalars(published.where(Star.id.in_(ids)))}
            star = next((available[id_] for id_ in ids if id_ in available), None)
    else:
        star = await db.scalar(published.where(Star.id == star_id))

    if star is None:
        raise HTTPException(status_code=404)

    likes_count = await db.scalar(
        select(func.count(Like.id)).where(Like.star_id == star.id)
    )

    is_liked = False
    if current_user is not None:
        is_liked = await db.scalar(
            select(select(Like.id).where(
                Like.star_id == star.id,
                Like.user_id == current_user["id"],
            ).exists())
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
        "is_liked": int(bool(is_liked)),
        "is_owner": int(
            current_user is not None
            and star.creator_id == current_user["id"]
        ),
        "description": star.description,
    }


@router.get("/native/catalog", response_model=list[NativeStarRead], tags=["Звёзды"])
async def native_catalog(db: AsyncSession = Depends(get_db)):
    likes_count = (
        select(func.count(Like.id)).where(Like.star_id == Star.id)
        .correlate(Star).scalar_subquery()
    )
    query = select(Star, likes_count).where(
        Star.status == "Опубликован", Star.clip_description.is_not(None)
    ).order_by(Star.id)
    return [
        {
            "id": star.id, "title": star.title, "description": star.description,
            "creator_id": star.creator_id, "is_owner": 0, "likes_count": likes,
            "image_url": media_url(star.image_url, "image"),
            "video_url": media_url(star.video_url, "video"),
            "received_date": star.received_date, "habitable_planets": star.habitable_planets,
            "clip_description": star.clip_description,
        }
        for star, likes in await db.execute(query)
    ]


@router.get("/catalog", response_model=CatalogRead,
    summary='Получить каталог',
    description='Доступно гостю. Страница опубликованных звёзд и общее число совпадений. Необязательная фильтрация по точной дате получения.',
    tags=['Звёзды'],
    responses={},
)
async def get_catalog_star(
    received_date: str = Query(default="", description="Дата YYYY-MM-DD; пустое значение — без фильтра"),
    page: int = Query(default=1, ge=1, le=10_000_000),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
):
    filter_date = None
    if received_date:
        try:
            filter_date = date.fromisoformat(received_date)
        except ValueError:
            raise HTTPException(status_code=422)

    conditions = [Star.status == "Опубликован"]
    if filter_date is not None:
        conditions.append(Star.received_date == filter_date)

    total = await db.scalar(select(func.count()).select_from(Star).where(*conditions))
    likes_count = (
        select(func.count(Like.id)).where(Like.star_id == Star.id)
        .correlate(Star).scalar_subquery()
    )
    query = (
        select(Star, likes_count).where(*conditions).order_by(Star.id)
        .offset((page - 1) * limit).limit(limit)
    )

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
            "is_owner": int(
            current_user is not None
            and star.creator_id == current_user["id"]
        ),
        })

    return {"data": stars, "total": total, "page": page, "limit": limit}




@router.post("/users", response_model=UserRead, status_code=201,
    summary='Регистрация',
    description='Доступно гостю. Создаёт пользователя. Пароль не возвращается. После регистрации выполните вход.',
    tags=['Пользователи'],
    responses={409: {'description': ''}},
)
async def register_user(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(select(User.id).where(User.username == payload.username))
    if existing is not None:
        return Response(status_code=409)
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

@router.post(
    "/users/login",
    response_model=UserRead,
    summary="Вход пользователя",
    tags=["Пользователи"],
    responses={401: {"description": ''}},
    description="Проверяет логин и пароль, создаёт сессию в Redis и устанавливает cookie.",
)
async def login_user(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(
        select(User).where(
            User.username == payload.username
        )
    )

    if user is None or user.password != payload.password:
        return Response(status_code=401)

    session_id = token_urlsafe(32)

    await redis_client.eval(
        CREATE_SESSION_SCRIPT,
        1,
        f"session:{session_id}",
        str(user.id),
        settings.SESSION_TTL,
    )

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.SESSION_TTL,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )

    return UserRead(
        id=user.id,
        username=user.username,
    )

@router.post(
    "/users/logout",
    summary="Выход пользователя",
    response_class=Response,
    tags=["Пользователи"],
    description="Удаляет текущую сессию из Redis и cookie из браузера.",
)
async def logout_user(request: Request):
    session_id = request.cookies.get(
        settings.SESSION_COOKIE_NAME
    )

    if session_id is not None:
        await redis_client.delete(
            f"session:{session_id}"
        )

    response = Response(status_code=200)

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
    )

    return response
