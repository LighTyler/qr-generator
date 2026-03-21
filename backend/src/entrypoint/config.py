from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent
env_file = find_dotenv() or (Path(__file__).resolve().parents[1] / ".env")
load_dotenv(env_file)


class DatabaseConfig(BaseSettings):
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    NAME: str

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
    )

    def get_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
        )


class ServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SERVICE_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    URL: str


class FrontendConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FRONTEND_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    URL: str


class APPConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    MODE: str
    NAME: str
    HOST: str
    PORT: int


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database: DatabaseConfig = DatabaseConfig()
    frontend: FrontendConfig = FrontendConfig()
    service: ServiceConfig = ServiceConfig()
    app: APPConfig = APPConfig()


def create_config() -> Config:
    return Config()


config = create_config()
