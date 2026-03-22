import re

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    username: str = Field(..., max_length=30)
    email: str = Field(..., max_length=255)
    id: str = Field(...)

class UserRequest(BaseModel):
    pass


class UserResponse(UserBase):
    pass


class RefreshToken(BaseModel):
    refresh_token: str = Field(...)


class TokenPair(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)


class AccessToken(BaseModel):
    access_token: str = Field(...)
