from pydantic import BaseModel

from schemas.user import UserResponse

class QRBase(BaseModel):
    user: UserResponse

class QRResponse(QRBase):
    salt: str

class QRRequest(QRBase):
    token: str