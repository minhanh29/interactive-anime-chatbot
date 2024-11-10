import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # database
    HOST: str
    PORT: str
    ROOT_USER: str
    ROOT_PASSWORD: str
    CURRENT_TENANT_DB: str

    # vector database
    SEARCH_INDEX: str
    SEARCH_ENDPOINT: str

    BOT_ENTITY_ID: int

    GEMINI_API_KEY: str

    class Config:
        env_file = "env/.dev.env"


settings = Settings()
