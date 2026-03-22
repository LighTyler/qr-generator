"""
Утилиты для работы с JWT токенами и хешированием паролей.

Предоставляет функции для:
- Создания и декодирования JWT токенов (access и refresh)
- Хеширования паролей с использованием bcrypt
- Проверки паролей

Использует настройки из конфигурации auth_jwt.
"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from entrypoint.config import config


def encode_jwt(
    payload: dict,
    private_key: str = None,
    algorithm: str = None,
    expire_timedelta: timedelta | None = None,
    expire_minutes: int = None,
) -> str:
    """
    Кодирование полезной нагрузки в JWT токен.
    
    Создаёт JWT токен с указанными данными и временем жизни.
    Автоматически добавляет поля exp (время истечения) и iat (время создания).
    
    Args:
        payload: Данные для кодирования в токен
        private_key: Приватный ключ для подписи (по умолчанию из конфига)
        algorithm: Алгоритм подписи (по умолчанию из конфига)
        expire_timedelta: Время жизни как timedelta (приоритет)
        expire_minutes: Время жизни в минутах (если не указан timedelta)
        
    Returns:
        str: Закодированный JWT токен
        
    Example:
        >>> token = encode_jwt({"sub": "123"}, expire_minutes=30)
    """
    if private_key is None:
        private_key = config.auth_jwt.PRIVATE_KEY
    if algorithm is None:
        algorithm = config.auth_jwt.ALGORITM
    
    to_encode = payload.copy()
    now = datetime.now(UTC)

    # Определение времени истечения токена
    if expire_timedelta:
        expire = now + expire_timedelta
    elif expire_minutes:
        expire = now + timedelta(minutes=expire_minutes)
    else:
        expire = now + timedelta(
            minutes=config.auth_jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    # Добавление стандартных claims
    to_encode.update(
        exp=expire,  # Время истечения
        iat=now,     # Время создания
    )
    
    # Кодирование токена
    encoded = jwt.encode(
        to_encode,
        private_key,
        algorithm=algorithm,
    )
    return encoded


def decode_jwt(
    token: str | bytes,
    public_key: str = None,
    algorithm: str = None,
) -> dict:
    """
    Декодирование JWT токена.
    
    Проверяет подпись и возвращает полезную нагрузку токена.
    
    Args:
        token: JWT токен для декодирования
        public_key: Публичный ключ для проверки подписи (по умолчанию из конфига)
        algorithm: Алгоритм подписи (по умолчанию из конфига)
        
    Returns:
        dict: Декодированная полезная нагрузка токена
        
    Raises:
        InvalidTokenError: Если токен невалиден или просрочен
        
    Example:
        >>> payload = decode_jwt(token)
        >>> user_id = payload.get("sub")
    """
    if public_key is None:
        public_key = config.auth_jwt.PUBLIC_KEY
    if algorithm is None:
        algorithm = config.auth_jwt.ALGORITM
    
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=[algorithm],
    )
    return decoded


def create_access_token(
    data: dict,
    expire_minutes: int = config.auth_jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """
    Создание access токена для авторизации.
    
    Access токен - короткоживущий токен для доступа к API.
    
    Args:
        data: Данные для включения в токен (обычно {"sub": user_id})
        expire_minutes: Время жизни в минутах (по умолчанию из конфига)
        
    Returns:
        str: Access JWT токен
    """
    return encode_jwt(
        payload=data,
        expire_minutes=expire_minutes,
    )


def create_refresh_token(data: dict) -> str:
    """
    Создание refresh токена для обновления access токена.
    
    Refresh токен - долгоживущий токен для получения новых access токенов.
    
    Args:
        data: Данные для включения в токен (обычно {"sub": user_id})
        
    Returns:
        str: Refresh JWT токен
    """
    return encode_jwt(
        payload=data,
        expire_timedelta=timedelta(
            days=config.auth_jwt.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    )


def hash_password(password: str) -> str:
    """
    Хеширование пароля с использованием bcrypt.
    
    Генерирует случайную соль и хеширует пароль.
    Результат включает соль, поэтому его можно напрямую сохранять в БД.
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        str: Хешированный пароль (включает соль)
        
    Note:
        bcrypt автоматически генерирует соль и включает её в результат.
        Один и тот же пароль будет давать разные хеши при каждом вызове.
    """
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode("utf-8")


def validate_password(password: str, hashed_password: str) -> bool:
    """
    Проверка пароля против хеша.
    
    Сравнивает пароль в открытом виде с хешированным паролем.
    
    Args:
        password: Пароль в открытом виде для проверки
        hashed_password: Хешированный пароль из БД
        
    Returns:
        bool: True если пароль совпадает, False иначе
    """
    return bcrypt.checkpw(
        password=password.encode(),
        hashed_password=hashed_password.encode("utf-8"),
    )
