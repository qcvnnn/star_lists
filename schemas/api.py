from pydantic import BaseModel, Field
from datetime import date

class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=20)

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

class PublishRequest(BaseModel):
    description: str
    received_date: date
    habitable_planets: int = Field(ge=0)

class LikeRequest(BaseModel):
    value: int = Field(ge=0, le=1)
