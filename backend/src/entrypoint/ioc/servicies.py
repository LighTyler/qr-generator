from dishka import Provider, Scope, provide

from core.uow import UnitOfWork

from repositories.qr import QRRepositoryI
from services.qr import QRService


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_user_service(
        self,
        uow: UnitOfWork,
        qr_repository: QRRepositoryI,
    ) -> QRService:
        return QRService(uow, qr_repository)
