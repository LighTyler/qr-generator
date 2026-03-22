"""
Утилиты для генерации и проверки QR-токенов.

Предоставляет функции для:
- Генерации составных QR-токенов (public + private части)
- Проверки QR-токенов
- Шифрования публичной части (user_id, username)
- Хеширования приватной части (email)

Структура QR-токена: "public_part.private_part"
- public_part: зашифрованные Fernet "user_id.username"
- private_part: SHA256 хеш "email + salt"
"""

from cryptography.fernet import Fernet

import hashlib
import time
import uuid
import secrets

# Генерация ключа шифрования Fernet
# Внимание: при перезапуске сервера ключ меняется, старые токены становятся невалидными
FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)


def generate_token(username: str, id: int, email: str) -> str:
    """
    Генерация QR-токена из данных пользователя.
    
    Создаёт составной токен из двух частей:
    - public: зашифрованные user_id и username
    - private: хеш email с уникальной солью
    
    Args:
        username: Имя пользователя
        id: ID пользователя
        email: Email пользователя
        
    Returns:
        tuple: (salt, token) где token = "public_part.private_part"
        
    Note:
        Salt нужно сохранить в БД для последующей проверки токена
        
    Example:
        >>> salt, token = generate_token("john", 123, "john@example.com")
        >>> # token = "gAAAAABh...abc.abc123..."
    """
    # Шифруем публичную часть: user_id.username
    public_token = encrypt_public(f"{id}.{username}")
    
    # Хешируем приватную часть: email + salt
    salt, private_token = hash_private_data(private=email)
    
    return hex, f"{public_token}.{private_token}"


def check(username: str, id: int, email: str, recieved_token: str, salt: str) -> bool:
    """
    Проверка QR-токена.
    
    Восстанавливает токен из данных пользователя и сравнивает с полученным.
    
    Args:
        username: Имя пользователя
        id: ID пользователя
        email: Email пользователя
        recieved_token: Токен для проверки (из QR-кода)
        salt: Соль из БД (использовалась при генерации)
        
    Returns:
        bool: True если токен валиден, False иначе
        
    Example:
        >>> is_valid = check("john", 123, "john@example.com", token, salt)
    """
    # Восстанавливаем публичную часть
    public_token = encrypt_public(f"{id}.{username}")
    
    # Восстанавливаем приватную часть с известной солью
    private_token = hash_private_data(private=email, salt=salt)
    
    # Собираем токен и сравниваем
    token = f"{public_token}.{private_token}"
    
    if recieved_token == token:
        return True
    return False


def encrypt_public(public: str) -> str:
    """
    Шифрование публичной части токена симметричным шифрованием Fernet.
    
    Fernet гарантирует:
    - Конфиденциальность (AES-128 в режиме CBC)
    - Целостность (HMAC-SHA256)
    - Уникальность (IV для каждого сообщения)
    
    Args:
        public: Строка для шифрования (обычно "user_id.username")
        
    Returns:
        str: Зашифрованная строка в base64 формате
        
    Note:
        Для расшифровки нужен тот же ключ FERNET_KEY
    """
    public_token = cipher.encrypt(public.encode())
    return public_token.decode()


def decrypt_public(public: str) -> tuple:
    """
    Расшифровка публичной части токена.
    
    Расшифровывает строку и разбивает на компоненты.
    
    Args:
        public: Зашифрованная строка (результат encrypt_public)
        
    Returns:
        tuple: Кортеж компонентов (user_id, username)
        
    Raises:
        cryptography.fernet.InvalidToken: Если токен невалиден
        
    Example:
        >>> user_id, username = decrypt_public(encrypted_part)
        >>> # user_id = "123", username = "john"
    """
    public_dec = cipher.decrypt(public.encode()).decode()
    return tuple(public_dec.split("."))


def hash_private_data(private: str, salt: str | None) -> str | tuple:
    """
    Хеширование приватных данных с солью.
    
    Использует SHA256 для создания необратимого хеша.
    
    Args:
        private: Приватные данные для хеширования (обычно email)
        salt: Соль для хеширования. Если None - генерируется новая
        
    Returns:
        str | tuple: 
            - Если salt is None: (salt, hash)
            - Если salt передан: hash
            
    Note:
        При генерации токена salt=None (генерируется новый)
        При проверке токена salt передаётся из БД
        
    Example:
        >>> # Генерация
        >>> salt, hash1 = hash_private_data("secret@email.com", None)
        >>> # Проверка
        >>> hash2 = hash_private_data("secret@email.com", salt)
        >>> assert hash1 == hash2
    """
    if salt == None:
        # Генерируем уникальную соль из timestamp и UUID
        salt = f"{time.time()}{uuid.uuid4()}"
        private_token = f'{private}{salt}'
        return salt, hashlib.sha256(private_token.encode()).hexdigest()
    else:
        # Используем переданную соль
        private_token = f'{private}{salt}'
        return hashlib.sha256(private_token.encode()).hexdigest()
