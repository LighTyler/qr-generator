"""
Реестр провайдеров для dependency injection.

Этот модуль предоставляет функцию для получения всех провайдеров DI,
которые используются для создания контейнера Dishka.

Порядок провайдеров важен - зависимости должны быть доступны
в момент когда они требуются другим провайдерам.
"""

from collections.abc import Iterable

from dishka import Provider
from dishka.integrations.fastapi import FastapiProvider

from entrypoint.ioc import (
    AuthProvider,
    ConfigProvider,
    DatabaseProvider,
    RepositoryProvider,
    ServiceProvider,
)


def get_providers() -> Iterable[Provider]:
    """
    Получение всех провайдеров для DI контейнера.
    
    Возвращает провайдеры в порядке, учитывающем зависимости между ними:
    1. DatabaseProvider - создаёт сессию БД (базовая зависимость)
    2. AuthProvider - зависит от сервисов и репозиториев
    3. ServiceProvider - зависит от репозиториев и UoW
    4. RepositoryProvider - зависит от сессии БД
    5. FastapiProvider - интеграция с FastAPI
    6. ConfigProvider - конфигурация приложения
    
    Returns:
        Iterable[Provider]: Кортеж всех провайдеров для регистрации в контейнере
    """
    return (
        DatabaseProvider(),     # Подключение к БД
        AuthProvider(),         # Аутентификация пользователей
        ServiceProvider(),      # Бизнес-сервисы
        RepositoryProvider(),   # Репозитории для работы с данными
        FastapiProvider(),      # Интеграция Dishka с FastAPI
        ConfigProvider(),       # Конфигурация приложения
    )
