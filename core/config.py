from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int = 5455
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    CURRENT_USER_ID: int = 1

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> URL:
        return URL.create(
            "postgresql+asyncpg", username=self.DB_USER, password=self.DB_PASSWORD,
            host=self.DB_HOST, port=self.DB_PORT, database=self.DB_NAME,
        )


settings = Settings()
