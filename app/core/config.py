import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "FastAPIApp")
    DEBUG: bool = os.getenv("DEBUG", False)
    CLIENT_URL: str = os.getenv("CLIENT_URL")
    DOCS_URL: str = os.getenv("DOCS_URL")
    DHAN_CLIENT_ID: str = os.getenv("DHAN_CLIENT_ID")
    DHAN_ACCESS_TOKEN: str = os.getenv("DHAN_ACCESS_TOKEN")
    MONGODB_URL: str = os.getenv("MONGODB_URL")


settings = Settings()
