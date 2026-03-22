from dishka import Provider, Scope, provide

from core.uow import UnitOfWork

from repositories.user import IUserRepository
from repositories.qr import QRRepositoryI
from services.user import UserService
from services.qr import QRService


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_user_service(
        self,
        user_repository: IUserRepository,
    ) -> UserService:
        return UserService(user_repository)

    @provide
    def get_qr_service(
        self,
        uow: UnitOfWork,
        qr_repository: QRRepositoryI,
    ) -> QRService:
        return QRService(uow, qr_repository)
