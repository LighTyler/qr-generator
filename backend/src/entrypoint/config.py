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


class AuthJWTConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AUTH_JWT_",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @property
    def PRIVATE_KEY(self):
        return self.SECRET_KEY

    @property
    def PUBLIC_KEY(self):
        return self.SECRET_KEY


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database: DatabaseConfig = DatabaseConfig()
    frontend: FrontendConfig = FrontendConfig()
    service: ServiceConfig = ServiceConfig()
    app: APPConfig = APPConfig()
    auth_jwt: AuthJWTConfig = AuthJWTConfig()


def create_config() -> Config:
    return Config()


config = create_config()
