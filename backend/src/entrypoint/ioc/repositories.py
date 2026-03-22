from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from core.uow import UnitOfWork
from repositories.qr import (
    QRRepository, QRRepositoryI
)

class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    @provide(provides=QRRepositoryI)
    def get_user_repository(self, session: AsyncSession) -> QRRepositoryI:
        return QRRepository(session)

    @provide
    def get_unit_of_work(self, session: AsyncSession) -> UnitOfWork:
        return UnitOfWork(session)
