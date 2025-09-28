import os
from pathlib import Path
from urllib.parse import quote_plus
from dataclasses import dataclass
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_DIR = Path(__file__).parent

try:
    load_dotenv(".env")
except Exception:
    pass


# todo: refactor
@dataclass
class Settings:
    DB_NAME = os.environ.get("DB_NAME")
    DB_PORT = os.environ.get("DB_PORT")
    DB_HOST = os.environ.get("DB_HOST")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = quote_plus(os.environ.get("DB_PASSWORD", ""))

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
    REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

    MONGO_USER = os.environ.get("MONGO_USER")
    MONGO_PASSWORD = quote_plus(os.environ.get("MONGO_PASSWORD", ""))
    MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
    MONGO_PORT = int(os.environ.get("MONGO_PORT", "27017"))
    MONGO_AUTH_DB = os.environ.get("MONGO_AUTH_DB", "admin")

    @property
    def database_url(self):
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def redis_url(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def mongo_url(self) -> str:
        return (
            f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}"
            f"@{self.MONGO_HOST}:{self.MONGO_PORT}/"
            f"?authSource={self.MONGO_AUTH_DB}"
        )


settings = Settings()
