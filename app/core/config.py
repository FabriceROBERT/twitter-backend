from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse
from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    
    # DB & App
    database_url: str
    front_url: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )

@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore

settings = get_settings()