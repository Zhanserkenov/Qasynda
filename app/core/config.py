from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:19660827@localhost:5432/qasynda_db"
    SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
    JWT_SECRET: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    class Config:
        env_file = ".env"

settings = Settings()