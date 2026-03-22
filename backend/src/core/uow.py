"""
Реализация паттерна Unit of Work.

Unit of Work (UoW) - паттерн для управления транзакциями базы данных.
Объединяет несколько операций с БД в одну атомарную транзакцию.

При выходе из контекста:
- Если была ошибка -> откат (rollback)
- Если всё успешно -> фиксация (commit)
"""

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """
    Unit of Work для управления транзакциями базы данных.
    
    Используется как асинхронный контекстный менеджер.
    Автоматически коммитит транзакцию при успешном выполнении
    или откатывает при возникновении исключения.
    
    Attributes:
        session (AsyncSession): Асинхронная сессия SQLAlchemy
    
    Example:
        >>> async with UnitOfWork(session) as uow:
        ...     await repository.create(data)
        ...     # При выходе автоматически commit
        >>> 
        >>> async with UnitOfWork(session) as uow:
        ...     await repository.create(data)
        ...     raise Exception()  # При выходе автоматически rollback
    """
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация Unit of Work.
        
        Args:
            session: Асинхронная сессия SQLAlchemy для выполнения операций
        """
        self.session = session

    async def __aenter__(self):
        """
        Вход в контекст. Возвращает self для использования.
        
        Returns:
            UnitOfWork: Экземпляр Unit of Work
        """
        return self

    async def __aexit__(self, exception_type, exception, traceback):
        """
        Выход из контекста с автоматическим управлением транзакцией.
        
        - Если exception_type не None (было исключение) -> rollback
        - Иначе (успешное выполнение) -> commit
        
        Args:
            exception_type: Тип исключения или None
            exception: Экземпляр исключения или None
            traceback: Traceback объекта или None
        """
        if exception_type:
            # При ошибке откатываем все изменения
            await self.session.rollback()
        else:
            # При успехе фиксируем все изменения
            await self.session.commit()
