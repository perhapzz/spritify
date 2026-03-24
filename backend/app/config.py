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

    # AI Pipeline
    replicate_api_token: Optional[str] = None  # env: REPLICATE_API_TOKEN
    ai_provider: str = "auto"  # "replicate" | "mock" | "auto"

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
