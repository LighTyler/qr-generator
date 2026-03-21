from typing import Protocol

from schemas.qr import QRRequest, QRResponse
from models.qr import QR


class QRRepositoryI(Protocol):
    async def create(self, qrdata: QRResponse) -> QR: ...
    async def get(self, qrdata: QRResponse) -> QR: ...
    async def update(self, qrdata: QRResponse) -> QR: ...
    async def delete(self, qr_id: int): ...

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
        query = select(QR).where(QR.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() 

    async def update(self, qrdata: QRResponse) -> QR:

        qr = await self.get(qrdata.id)
        if not qr:
            return None
        
        update_data = qrdata.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(qr, field, value)
        
        await self.session.flush()
        await self.session.refresh(qr)
        return qr

    async def delete(self, qr_id: int) -> bool:

        qr = await self.get(qr_id)
        
        if not qr:
            return False
        
        await self.session.delete(qr)
        
        await self.session.flush()
        
        return True