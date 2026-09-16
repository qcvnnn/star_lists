from datetime import date, datetime, timezone
from fastapi import APIRouter, Request, Query, HTTPException, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from core.config import settings
from models import Star, Like, User
from data.media import media_url, star_media


router = APIRouter()
templates = Jinja2Templates(directory="templates")

CURRENT_USER_ID = settings.CURRENT_USER_ID


@router.get("/draft")
async def open_draft(request: Request, db: AsyncSession = Depends(get_db)):
    star = await db.scalar(
        select(Star).where(
            Star.status == "Черновик",
            Star.creator_id == CURRENT_USER_ID,
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="add.html",
        context={"star": star, "media": await star_media(star)},
    )


@router.post("/stars")
async def create_star(
    title: str = Form(..., min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    title = title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Введите название звезды")

    user = await db.scalar(
        select(User).where(User.id == CURRENT_USER_ID).with_for_update()
    )
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    draft = await db.scalar(
        select(Star).where(
            Star.creator_id == CURRENT_USER_ID,
            Star.status == "Черновик",
        )
    )
    if draft is not None:
        return RedirectResponse(url="/draft", status_code=303)

    star = Star(
        title=title,
        status="Черновик",
        creator_id=CURRENT_USER_ID,
    )
    db.add(star)
    await db.commit()

    return RedirectResponse(url="/draft", status_code=303)


@router.post("/stars/{star_id}/publish")
async def publish_star(
    star_id: int,
    title: str = Form(..., min_length=1, max_length=100),
    description: str = Form(..., min_length=1),
    received_date: date = Form(...),
    habitable_planets: int = Form(..., ge=0),
    db: AsyncSession = Depends(get_db),
):
    title = title.strip()
    description = description.strip()
    if not title or not description:
        raise HTTPException(status_code=422, detail="Заполните название и описание")

    star = await db.scalar(
        select(Star).where(
            Star.id == star_id,
            Star.creator_id == CURRENT_USER_ID,
            Star.status == "Черновик",
        ).with_for_update()
    )
    if star is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    star.title = title
    star.description = description
    star.received_date = received_date
    star.habitable_planets = habitable_planets
    star.status = "Опубликован"
    star.formed_at = datetime.now(timezone.utc)
    await db.commit()
    return RedirectResponse(url=f"/feed?id={star_id}", status_code=303)


@router.post("/stars/{star_id}/delete")
async def delete_star(star_id: int, db: AsyncSession = Depends(get_db)):
    # Raw SQL, как в методичке: параметризованный UPDATE без ORM.
    result = await db.execute(
        text("UPDATE stars SET status = :deleted "
             "WHERE id = :id AND creator_id = :user_id AND status = :published"),
        {"deleted": "Удален", "id": star_id, "user_id": CURRENT_USER_ID,
         "published": "Опубликован"},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Звезда не найдена")
    await db.commit()
    return RedirectResponse(url="/catalog", status_code=303)


@router.get("/feed")
async def get_star_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    star_id: int | None = Query(default=None, alias="id"),
    next_star: bool = Query(default=False, alias="next"),
):
    published = select(Star).where(Star.status == "Опубликован")

    if star_id is None:
        star = await db.scalar(published.order_by(Star.id).limit(1))
    else:
        star = await db.scalar(published.where(Star.id == star_id))

    if star is None:
        raise HTTPException(status_code=404, detail="Звезда не найдена")

    if next_star:
        following = await db.scalar(
            published.where(Star.id > star.id).order_by(Star.id).limit(1)
        )
        star = following if following is not None else await db.scalar(
            published.order_by(Star.id).limit(1)
        )
        if star is None:
            raise HTTPException(status_code=404, detail="Звезда не найдена")

    likes_count = await db.scalar(
        select(func.count(Like.id)).where(Like.star_id == star.id)
    )
    description = star.description or ""
    description_preview = description
    description_rest = ""

    if len(description) > 120:
        split_at = description.rfind(" ", 0, 121)
        if split_at == -1:
            split_at = 120
        description_preview = description[:split_at]
        description_rest = description[split_at:].lstrip()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "star": star,
            "media": await star_media(star),
            "likes_count": likes_count,
            "description_preview": description_preview,
            "description_rest": description_rest,
        },
    )


@router.get("/catalog")
async def get_catalog_star(
    request: Request,
    received_date: str = "",
    db: AsyncSession = Depends(get_db),
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
    checked_media = {}
    for star, likes_count in await db.execute(query):
        stars.append({
            "id": star.id,
            "creator_id": star.creator_id,
            "title": star.title,
            "image_url": await media_url(star.image_url, "image", checked_media),
            "video_url": await media_url(star.video_url, "video", checked_media),
            "received_date": star.received_date,
            "habitable_planets": star.habitable_planets,
            "likes_count": likes_count,
        })

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "stars": stars,
            "current_user_id": CURRENT_USER_ID,
            "received_date": filter_date.isoformat() if filter_date else "",
        },
    )
