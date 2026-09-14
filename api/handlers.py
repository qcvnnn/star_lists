from datetime import date
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from data.collections import star_lists_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")



@router.get("/draft")
def open_draft(request: Request):
    star = None
    index = 0
    for _ in star_lists_db:
        if star_lists_db[index]["status"] == "Черновик":
            star = star_lists_db[index]
            break
        index += 1

    if star is None:
        raise HTTPException(status_code=404, detail="Черновик не найден")

    return templates.TemplateResponse(
        request=request,
        name="add.html",
        context={"star": star},
    )

@router.get("/feed")
def get_star_detail(
    request: Request,
    star_id: int | None = Query(default=None, alias="id"),
    next_star: bool = Query(default=False, alias="next"),
):
    star = None
    if not star_lists_db:
        raise HTTPException(status_code=404, detail="Звёзды не найдены")
    if star_id is None:
        index = 0
        for _ in star_lists_db:
            if star_lists_db[index]["status"] == 'Опубликован':
                star = star_lists_db[index]
                break
            index += 1
    else:
        star = next((s for s in star_lists_db if s["id"] == star_id and s["status"] == 'Опубликован'), None)

    if star is None:
        raise HTTPException(status_code=404, detail="Звезда не найдена")

    if next_star:
        index = star_lists_db.index(star)
        for _ in star_lists_db:
            index = (index + 1) % len(star_lists_db)
            star = star_lists_db[index]
            if star['status'] == 'Опубликован':
                break

    likes_count = len(star["likes"])
    description = star["description"]
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
            "likes_count": likes_count,
            "description_preview": description_preview,
            "description_rest": description_rest,
        },
    )


@router.get("/catalog")
def get_catalog_star(request: Request, received_date: str = ""):
    filter_date = None
    if received_date:
        try:
            filter_date = date.fromisoformat(received_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Дата должна быть в формате ГГГГ-ММ-ДД")

    stars = []
    for star in star_lists_db:
        if star["status"] != "Опубликован":
            continue
        if filter_date is not None and star["date"] != filter_date:
            continue

        card = star.copy()
        card["likes_count"] = len(star["likes"])
        stars.append(card)

    return templates.TemplateResponse(
        request=request,
        name="catalog.html",
        context={
            "stars": stars,
            "received_date": filter_date.isoformat() if filter_date else "",
        },
    )
