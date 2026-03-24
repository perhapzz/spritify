from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Spritify"
    debug: bool = False

    # Azure Storage
    azure_storage_connection_string: Optional[str] = None
    azure_storage_container_uploads: str = "uploads"
    azure_storage_container_outputs: str = "outputs"

    # Use local storage if Azure not configured
    use_local_storage: bool = True

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
