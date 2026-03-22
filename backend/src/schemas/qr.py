from pydantic import BaseModel

from schemas.user import UserResponse


class QRBase(BaseModel):
    user: UserResponse


class QRResponse(QRBase):
    salt: str
    connection_id: str | None = None


class QRRequest(BaseModel):
    token: str


class CheckTokenRequest(BaseModel):
    token: str


class CheckTokenResponse(BaseModel):
    valid: bool
    user_id: int | None = None
    username: str | None = None
    email: str | None = None


class WSAuthMessage(BaseModel):
    """Сообщение для авторизации через WebSocket"""
    access_token: str
