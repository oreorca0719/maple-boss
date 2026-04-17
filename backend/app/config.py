from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Nexon Open API
    nexon_api_key: str = ""

    # LLM (Upstage)
    upstage_api_key: str = ""
    llm_model: str = "solar-pro3"
    llm_timeout: int = 30

    # AWS
    aws_region: str = "ap-northeast-2"

    # DynamoDB
    dynamodb_table_name: str = "maple-boss-scheduler"
    dynamodb_endpoint_url: str | None = None  # None = 실제 AWS, 값이 있으면 DynamoDB Local

    # Application
    app_env: str = "production"
    app_secret_key: str = "change-this-secret"
    app_cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",")]

    @property
    def is_local(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
