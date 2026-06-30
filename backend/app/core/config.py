from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/library.db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 元数据源 (豆瓣官方 API 2019 起不再开放新 key, 改用 Open Library + Google Books)
    # 这两个源都无需 key, 见 app/services/douban.py
    META_TIMEOUT_SECONDS: int = 10

    # 上传
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB

    # CORS
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# 确保数据目录存在
Path("./data").mkdir(parents=True, exist_ok=True)
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
