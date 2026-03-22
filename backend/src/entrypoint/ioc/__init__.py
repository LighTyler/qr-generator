"""
Экспорт провайдеров dependency injection (Dishka).

Этот модуль собирает все DI провайдеры в одном месте для удобного импорта.

Available providers:
    - AuthProvider: Провайдер аутентификации (извлечение пользователя из JWT)
    - ConfigProvider: Провайдер конфигурации приложения
    - DatabaseProvider: Провайдер подключения к базе данных
    - RepositoryProvider: Провайдер репозиториев для работы с данными
    - ServiceProvider: Провайдер бизнес-сервисов
"""

from entrypoint.ioc.auth import AuthProvider
from entrypoint.ioc.config import ConfigProvider
from entrypoint.ioc.database import DatabaseProvider
from entrypoint.ioc.repositories import RepositoryProvider
from entrypoint.ioc.servicies import ServiceProvider

__all__ = [
    "AuthProvider",
    "DatabaseProvider",
    "RepositoryProvider",
    "ServiceProvider",
    "ConfigProvider",
]
