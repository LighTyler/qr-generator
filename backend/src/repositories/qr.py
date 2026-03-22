from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.qr import QRRequest, QRResponse
from models.qr import QR


class QRRepositoryI(Protocol):
    async def create(self, qrdata: QRResponse) -> QR: ...
    async def get(self, qrdata: QRRequest) -> QR: ...
    async def get_by_user_id(self, user_id: int) -> QR | None: ...
    async def get_by_connection_id(self, connection_id: str) -> QR | None: ...
    async def update(self, qrdata: QRResponse) -> QR: ...
    async def update_connection_id(self, user_id: int, connection_id: str | None) -> bool: ...
    async def delete(self, user_id: int) -> bool: ...
    async def delete_by_connection_id(self, connection_id: str) -> bool: ...


class QRRepository(QRRepositoryI):
    def __init__(
            self,
            session: AsyncSession,
        ):
            self.session = session

    async def create(self, qrdata: QRResponse) -> QR:
        qr = QR(
            user_id=qrdata.user.id,
            username=qrdata.user.username,
            email=qrdata.user.email,
            salt=qrdata.salt,
            connection_id=qrdata.connection_id,
        )
        self.session.add(qr)
        await self.session.flush()
        await self.session.refresh(qr)
        return qr
    
    async def get(self, qrdata: QRRequest) -> QR | None:
        """Получить запись по токену (через расшифровку public части)."""
        from utils.utils import decrypt_public
        
        parts = qrdata.token.split(".")
        if len(parts) < 2:
            return None
        
        public_part = parts[0]
        try:
            user_id, username = decrypt_public(public_part)
            user_id = int(user_id)
        except Exception:
            return None
        
        return await self.get_by_user_id(user_id)

    async def get_by_user_id(self, user_id: int) -> QR | None:
        """Получить запись по ID пользователя."""
        query = select(QR).where(QR.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_connection_id(self, connection_id: str) -> QR | None:
        """Получить запись по connection_id."""
        query = select(QR).where(QR.connection_id == connection_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, qrdata: QRResponse) -> QR | None:
        qr = await self.get_by_user_id(qrdata.user.id)
        if not qr:
            # Создаём новую запись если не существует
            return await self.create(qrdata)
        
        qr.username = qrdata.user.username
        qr.email = qrdata.user.email
        qr.salt = qrdata.salt
        if qrdata.connection_id is not None:
            qr.connection_id = qrdata.connection_id
        
        await self.session.flush()
        await self.session.refresh(qr)
        return qr

    async def update_connection_id(self, user_id: int, connection_id: str | None) -> bool:
        """Обновить только connection_id для записи."""
        qr = await self.get_by_user_id(user_id)
        if not qr:
            return False
        
        qr.connection_id = connection_id
        await self.session.flush()
        return True

    async def delete(self, user_id: int) -> bool:
        """Удалить запись по user_id."""
        qr = await self.get_by_user_id(user_id)
        
        if not qr:
            return False
        
        await self.session.delete(qr)
        await self.session.flush()
        return True

    async def delete_by_connection_id(self, connection_id: str) -> bool:
        """Удалить запись по connection_id."""
        qr = await self.get_by_connection_id(connection_id)
        
        if not qr:
            return False
        
        await self.session.delete(qr)
        await self.session.flush()
        return True