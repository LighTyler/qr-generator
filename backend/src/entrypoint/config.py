"""
Конфигурация приложения через переменные окружения.

Использует pydantic-settings для валидации и загрузки конфигурации из .env файла.
Все настройки разделены на логические группы (база данных, сервисы, аутентификация).

Структура конфигурации:
- DatabaseConfig: Настройки подключения к PostgreSQL
- ServiceConfig: URL основного сервиса
- FrontendConfig: URL фронтенда (для CORS)
- APPConfig: Общие настройки приложения
- AuthJWTConfig: Настройки JWT аутентификации
"""

from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Базовая директория проекта (backend/)
BASE_DIR = Path(__file__).parent.parent.parent

# Поиск и загрузка .env файла
env_file = find_dotenv() or (Path(__file__).resolve().parents[1] / ".env")
load_dotenv(env_file)


class DatabaseConfig(BaseSettings):
    """
    Конфигурация подключения к PostgreSQL базе данных.
    
    Переменные окружения (с префиксом POSTGRES_):
        POSTGRES_USER: Имя пользователя БД
        POSTGRES_PASSWORD: Пароль пользователя БД
        POSTGRES_HOST: Хост БД
        POSTGRES_PORT: Порт БД
        POSTGRES_NAME: Имя базы данных
    
    Example:
        >>> db_config = DatabaseConfig()
        >>> url = db_config.get_db_url()
        >>> # postgresql+asyncpg://user:pass@host:port/dbname
    """
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    NAME: str

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",  # Префикс для переменных окружения
    )

    def get_db_url(self) -> str:
        """
        Формирование URL для подключения к БД через asyncpg.
        
        Returns:
            str: URL в формате postgresql+asyncpg://user:pass@host:port/dbname
        """
        return (
            f"postgresql+asyncpg://"
            f"{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
        )


class ServiceConfig(BaseSettings):
    """
    Конфигурация основного сервиса.
    
    Используется для взаимодействия с основным сервером аутентификации.
    
    Переменные окружения (с префиксом SERVICE_):
        SERVICE_URL: URL основного сервиса (например, http://localhost:8000)
    """
    model_config = SettingsConfigDict(
        env_prefix="SERVICE_",
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорировать лишние переменные
    )

    URL: str


class FrontendConfig(BaseSettings):
    """
    Конфигурация фронтенда.
    
    Используется для настройки CORS - разрешённых источников запросов.
    
    Переменные окружения (с префиксом FRONTEND_):
        FRONTEND_URL: URL фронтенда (например, http://localhost:3000)
    """
    model_config = SettingsConfigDict(
        env_prefix="FRONTEND_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    URL: str


class APPConfig(BaseSettings):
    """
    Общие настройки приложения.
    
    Переменные окружения (с префиксом APP_):
        APP_MODE: Режим работы (dev, prod, test)
        APP_NAME: Название приложения
        APP_HOST: Хост для запуска сервера
        APP_PORT: Порт для запуска сервера
    """
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
    """
    Конфигурация JWT аутентификации.
    
    Переменные окружения (с префиксом AUTH_JWT_):
        AUTH_JWT_SECRET_KEY: Секретный ключ для подписи токенов
        AUTH_JWT_ALGORITM: Алгоритм подписи (по умолчанию HS256)
        AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Время жизни access токена
        AUTH_JWT_REFRESH_TOKEN_EXPIRE_DAYS: Время жизни refresh токена
    
    Note:
        В production SECRET_KEY должен быть надёжным и храниться в секрете!
    """
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
        """
        Приватный ключ для подписи токенов.
        
        В данной реализации используется симметричное шифрование (HS256),
        поэтому приватный и публичный ключи совпадают.
        
        Returns:
            str: Секретный ключ
        """
        return self.SECRET_KEY

    @property
    def PUBLIC_KEY(self):
        """
        Публичный ключ для проверки подписи токенов.
        
        В данной реализации используется симметричное шифрование (HS256),
        поэтому публичный и приватный ключи совпадают.
        
        Returns:
            str: Секретный ключ
        """
        return self.SECRET_KEY


class Config(BaseSettings):
    """
    Главная конфигурация приложения.
    
    Агрегирует все конфигурации в одном месте.
    Используется для dependency injection через Dishka.
    
    Attributes:
        database (DatabaseConfig): Конфигурация БД
        frontend (FrontendConfig): Конфигурация фронтенда
        service (ServiceConfig): Конфигурация основного сервиса
        app (APPConfig): Общие настройки приложения
        auth_jwt (AuthJWTConfig): Настройки JWT
    """
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
    """
    Фабрика для создания конфигурации.
    
    Returns:
        Config: Объект конфигурации приложения
    """
    return Config()


# Глобальный экземпляр конфигурации
config = create_config()
