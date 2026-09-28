
DEFAULT_IMAGE = "/static/media/default-star.jpg"
DEFAULT_VIDEO = "/static/media/default-star.mp4"


def media_url(url: str | None, kind: str) -> str:
    fallback = DEFAULT_IMAGE if kind == "image" else DEFAULT_VIDEO
    return (url or "").strip() or fallback


def star_media(star) -> dict:
    return {
        "image_url": media_url(star.image_url if star else None, "image"),
        "video_url": media_url(star.video_url if star else None, "video"),
    }
