# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    version: str
    DATABASE: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore"          
    )


settings = Settings()
