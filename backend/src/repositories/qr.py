from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.qr import QRRequest, QRResponse
from models.qr import QR


class QRRepositoryI(Protocol):
    async def create(self, qrdata: QRResponse) -> QR: ...
    async def get(self, qrdata: QRResponse) -> QR: ...
    async def update(self, qrdata: QRResponse) -> QR: ...
    async def delete_user(self, qr_id: int) -> bool: ...
    async def delete_note(self, qr_id: int) -> bool: ...

class QRRepository(QRRepositoryI):
    def __init__(
            self,
            session: AsyncSession,
        ):
            self.session = session
    async def create(self, qrdata: QRResponse) -> QR:
        qr = QR(**qrdata.model_dump()) 
        self.session.add(qr)
        await self.session.flush()
        await self.session.refresh(qr)
        return qr
    
    async def get(self, qr_id: int) -> QR:
        query = select(QR).where(QR.id == qr_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() 

    async def update(self, qrdata: QRResponse) -> QR:

        qr = await self.get(qrdata.user.id)
        if not qr:
            return None
        
        update_data = qrdata.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(qr, field, value)
        
        await self.session.flush()
        await self.session.refresh(qr)
        return qr

    async def delete_user(self, qr_id: int) -> bool:

        qr = await self.get(qr_id)
        
        if not qr:
            return False
        
        qr.timestamp = None
        
        await self.session.flush()
        
        return True

    async def delete_timestamp(self, qr_id: int) -> bool:

        qr = await self.get(qr_id)

        if not qr:
            return False

        await self.session.delete(qr.timestamp)

        await self.session.flush()

        return True