"""
Pydantic схемы для пользователей.

Содержит модели для:
- Создания пользователя (UserCreate, UserCreateConsole)
- Обновления пользователя (UserUpdate)
- Ответов с данными пользователя (UserResponse)
- Работы с JWT токенами (RefreshToken, TokenPair, AccessToken)
"""

import re

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """
    Базовая схема пользователя с основными полями.
    
    Attributes:
        username (str): Имя пользователя (макс. 30 символов)
        email (str): Email адрес (макс. 255 символов)
    """
    username: str = Field(..., max_length=30)
    email: str = Field(..., max_length=255)


class UserRequest(BaseModel):
    """
    Запрос для получения пользователя по ID.
    
    Attributes:
        id (int): Идентификатор пользователя
    """
    id: int = Field(...)


class UserResponse(UserBase):
    """
    Ответ с данными пользователя.
    
    Наследует поля от UserBase и добавляет:
        id (int): Идентификатор пользователя
        role (str): Роль пользователя (по умолчанию 'user')
    """
    id: int = Field(...)
    role: str = Field(default="user")


class UserCreate(BaseModel):
    """
    Схема для создания нового пользователя через API.
    
    Attributes:
        username (str): Имя пользователя (макс. 30 символов)
        email (str): Email адрес (макс. 255 символов)
        password (str): Пароль в открытом виде (макс. 255 символов)
    
    Note:
        Пароль будет захеширован перед сохранением в БД
    """
    username: str = Field(..., max_length=30)
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=255)


class UserCreateConsole(BaseModel):
    """
    Схема для создания пользователя через консольную команду.
    
    Отличается от UserCreate возможностью указать роль при создании.
    
    Attributes:
        username (str): Имя пользователя (макс. 30 символов)
        email (str): Email адрес (макс. 255 символов)
        password (str): Пароль в открытом виде (макс. 255 символов)
        role (str): Роль пользователя (по умолчанию 'user')
    
    Note:
        Используется скриптом create_user.py для создания администраторов
    """
    username: str = Field(..., max_length=30)
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=255)
    role: str = Field(default="user")


class UserUpdate(BaseModel):
    """
    Схема для обновления данных пользователя.
    
    Все поля опциональны - можно обновить только нужные.
    
    Attributes:
        username (str | None): Новое имя пользователя (опционально)
        email (str | None): Новый email адрес (опционально)
    """
    username: str | None = None
    email: str | None = None


class RefreshToken(BaseModel):
    """
    Схема для запроса обновления access токена.
    
    Attributes:
        refresh_token (str): Refresh токен для получения новой пары токенов
    """
    refresh_token: str = Field(...)


class TokenPair(BaseModel):
    """
    Пара JWT токенов для аутентификации.
    
    Attributes:
        access_token (str): Access токен для авторизации запросов (короткоживущий)
        refresh_token (str): Refresh токен для обновления access токена (долгоживущий)
    """
    access_token: str = Field(...)
    refresh_token: str = Field(...)


class AccessToken(BaseModel):
    """
    Схема с одним access токеном.
    
    Используется когда refresh токен не требуется в ответе.
    
    Attributes:
        access_token (str): Access токен для авторизации запросов
    """
    access_token: str = Field(...)
