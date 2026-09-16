"""Подстановка локальных файлов для пустых и недоступных URL."""
import httpx

DEFAULT_IMAGE = "/static/media/default-star.jpg"
DEFAULT_VIDEO = "/static/media/default-star.mp4"


async def media_url(url: str | None, kind: str, checked: dict) -> str:
    fallback = DEFAULT_IMAGE if kind == "image" else DEFAULT_VIDEO
    if not url or not url.strip():
        return fallback
    url = url.strip()
    key = (url, kind)
    if key not in checked:
        try:
            # Проверяем заголовки, не скачивая видео при открытии страницы.
            async with httpx.AsyncClient(timeout=1.5, follow_redirects=True, trust_env=False) as client:
                response = await client.head(url)
                if response.status_code in (405, 501):
                    async with client.stream("GET", url, headers={"Range": "bytes=0-0"}) as response:
                        available = response.is_success and response.headers.get("content-type", "").startswith(kind + "/")
                else:
                    available = response.is_success and response.headers.get("content-type", "").startswith(kind + "/")
        except (httpx.HTTPError, httpx.InvalidURL):
            available = False
        checked[key] = url if available else fallback
    return checked[key]


async def star_media(star) -> dict:
    checked = {}
    return {
        "image_url": await media_url(star.image_url if star else None, "image", checked),
        "video_url": await media_url(star.video_url if star else None, "video", checked),
    }
