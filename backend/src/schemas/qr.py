from pydantic import BaseModel


class QRResponse(BaseModel):
    username: str
    email: str
    salt: str


class QRRequest(BaseModel):
    username: str
    email: str
    token: str