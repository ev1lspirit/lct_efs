import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_DIR = Path(__file__).parent

try:
    load_dotenv(".env")
except Exception:
    pass


# todo: refactor
class Settings(BaseSettings):
    DB_NAME = os.environ.get("DB_NAME")
    DB_PORT = os.environ.get("DB_PORT")
    DB_HOST = os.environ.get("DB_HOST")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = quote_plus(os.environ.get("DB_PASSWORD", ""))

    @property
    def database_url(self):
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
