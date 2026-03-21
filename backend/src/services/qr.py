from datetime import datetime, timedelta

from schemas.qr  import UserResponse, QRRequest, QRResponse
from utils.utils import generate_token, check
from repositories.qr import QRRepositoryI



class QRService:
    def __init__(
        self,
        uow: UnitOfWork,
        qr_repository: QRRepositoryI,
    ):
        self.uow = uow
        self.qr_repository = qr_repository

    async def generate_token(self, user: UserResponse.email, ) -> str:
        user_dict = user.model_dump()
        salt, token = generate_token(**user_dict)
        qr_resp = QRResponse(user=user, salt=salt)
        async with self.uow:
            await self.qr_repository.update(qr_resp)

        return token

    async def check_token(self, user: QRRequest) -> bool:
        user_rep = await self.qr_repository.get(user.id)
        token = check(
            username=user.username,
            id=user.id,
            email=user.email,
            salt=user_rep.salt,
            )
        
        time_valid = datetime.now() < (user_rep.timestamp + timedelta(minutes=5))
        
        async with self.uow:
            await self.qr_repository.delete(user.id)
        
        return token and time_valid




