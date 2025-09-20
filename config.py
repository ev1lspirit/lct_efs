from pathlib import Path
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent

try:
    load_dotenv(".env")
except Exception:
    pass


class Settings:
    pass



settings = Settings()
