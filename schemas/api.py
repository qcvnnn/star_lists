from pydantic import BaseModel, Field
from datetime import date

class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50, description="Логин пользователя", examples=["student"])
    password: str = Field(min_length=1, max_length=20, description="Пароль", json_schema_extra={"format": "password"})

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50, description="Логин пользователя", examples=["student"])
    password: str = Field(min_length=1, max_length=20, description="Пароль", json_schema_extra={"format": "password"})

class UserRead(BaseModel):
    id: int
    username: str

class StarRead(BaseModel):
    id: int
    creator_id: int
    title: str
    image_url: str
    video_url: str
    received_date: date | None
    habitable_planets: int | None
    likes_count: int
    is_owner: int

class StarDetailRead(StarRead):
    description: str | None

class CatalogRead(BaseModel):
    data: list[StarRead]
    total: int
    page: int
    limit: int

class NativeStarRead(StarDetailRead):
    clip_description: str

class PublishRequest(BaseModel):
    description: str = Field(description="Описание звёздной системы")
    received_date: date = Field(description="Дата получения", examples=["2026-10-13"])
    habitable_planets: int = Field(ge=0, description="Число планет в зоне обитаемости")

class LikeRequest(BaseModel):
    value: int = Field(ge=0, le=1, description="1 — поставить лайк, 0 — снять", examples=[1])


class FeedRead(StarDetailRead):
    is_liked: int = Field(ge=0, le=1)
