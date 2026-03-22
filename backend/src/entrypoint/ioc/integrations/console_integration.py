"""
Интеграция Dishka для консольных команд.

Предоставляет декоратор @inject для использования dependency injection
в консольных скриптах (например, create_user.py).

В отличие от FastAPI интеграции, здесь нет автоматического запроса,
поэтому нужно явно передавать dishka_container в kwargs.
"""

from collections.abc import Callable
from typing import TypeVar

from dishka.integrations.base import wrap_injection

# TypeVar для сохранения типа декорируемой функции
T = TypeVar("T")


def inject(func: Callable) -> Callable:
    """
    Декоратор для внедрения зависимостей в консольные команды.
    
    Позволяет использовать зависимости Dishka в асинхронных функциях.
    Контейнер должен быть передан в kwargs с ключом "dishka_container".
    
    Args:
        func: Асинхронная функция для декорирования
        
    Returns:
        Callable: Обёрнутая функция с поддержкой DI
        
    Example:
        >>> @inject
        ... async def create_user(
        ...     user_service: FromDishka[UserService],
        ...     dishka_container: AsyncContainer,
        ... ):
        ...     await user_service.create(...)
        ... 
        >>> async with container_context() as container:
        ...     await create_user(dishka_container=container)
    """
    return wrap_injection(
        func=func,
        # Извлекаем контейнер из kwargs
        container_getter=lambda args, kwargs: kwargs["dishka_container"],
        manage_scope=True,  # Автоматическое управление scope
        is_async=True,  # Функция асинхронная
    )
