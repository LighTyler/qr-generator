"""
Настройка и инициализация FastAPI приложения.

Этот модуль отвечает за:
- Создание FastAPI приложения
- Настройку lifespan (запуск/остановка)
- Настройку CORS middleware
- Создание DI контейнера Dishka
- Подключение роутеров
"""

import logging
from collections.abc import Iterable
from contextlib import asynccontextmanager

from dishka import Provider, make_async_container
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from entrypoint.config import Config, create_config, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager для управления жизненным циклом приложения.
    
    Выполняется при запуске и остановке приложения.
    Здесь можно инициализировать соединения, пулы и т.д.
    
    Args:
        app: Экземпляр FastAPI приложения
        
    Yields:
        None: Контроль передаётся в приложение
    """
    logging.info("Application starting up")
    yield
    logging.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Фабрика для создания FastAPI приложения.
    
    Создаёт экземпляр FastAPI с настроенным lifespan.
    
    Returns:
        FastAPI: Настроенный экземпляр приложения
    """
    app = FastAPI(lifespan=lifespan)
    return app


def create_async_container(providers: Iterable[Provider]):
    """
    Создание асинхронного DI контейнера Dishka.
    
    Объединяет все провайдеры зависимостей и добавляет
    конфигурацию в контекст контейнера.
    
    Args:
        providers: Итерируемый объект с провайдерами Dishka
        
    Returns:
        AsyncContainer: Асинхронный контейнер зависимостей
    """
    config = create_config()
    return make_async_container(
        *providers,
        context={Config: config},  # Добавляем конфигурацию в контекст
    )


def configure_app(app: FastAPI, root_router: APIRouter) -> None:
    """
    Подключение роутеров к приложению.
    
    Args:
        app: Экземпляр FastAPI приложения
        root_router: Главный роутер с вложенными роутерами
    """
    app.include_router(root_router)


def configure_middlewares(app: FastAPI) -> None:
    """
    Настройка middleware для приложения.
    
    Добавляет CORS middleware для разрешения запросов
    от фронтенда и основного сервиса.
    
    Args:
        app: Экземпляр FastAPI приложения
    
    Note:
        В production следует ограничить allow_origins конкретными доменами
    """
    app.add_middleware(
        CORSMiddleware,
        # Разрешённые источники (фронтенд и основной сервис)
        allow_origins=[config.frontend.URL, config.service.URL],
        # Разрешить передачу cookies и authorization headers
        allow_credentials=True,
        # Разрешить все HTTP методы
        allow_methods=["*"],
        # Разрешить все заголовки
        allow_headers=["*"],
    )
