"""
Генератор RSA ключей для JWT аутентификации.

Создаёт пару RSA ключей (приватный и публичный) для подписи и проверки JWT токенов.
Также генерирует JWK (JSON Web Key) и JWKS (JSON Web Key Set) для использования
с внешними сервисами и фронтендом.

Выходные файлы:
- jwt_private_key.pem: Приватный ключ для подписи токенов (секретный!)
- jwt_public_key.pem: Публичный ключ для проверки подписи
- jwt_public_jwk.json: Публичный ключ в формате JWK
- jwt_public_jwks.json: JWKS (набор ключей) для OIDC-совместимых систем

Использование:
    python generate_jwt_certs.py

Note:
    - Приватный ключ должен храниться в секрете!
    - Размер ключа: 4096 бит (безопасно для production)
    - Алгоритм: RS256 (RSA + SHA-256)
"""

import json
import uuid
import base64

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

# Директория для сохранения ключей
OUT_DIR = Path("../certs")
OUT_DIR.mkdir(exist_ok=True)

# Пути к файлам ключей
PRIVATE_KEY_FILE = OUT_DIR / "jwt_private_key.pem"
PUBLIC_KEY_FILE = OUT_DIR / "jwt_public_key.pem"
PUBLIC_JWK_FILE = OUT_DIR / "jwt_public_jwk.json"
PUBLIC_JWKS_FILE = OUT_DIR / "jwt_public_jwks.json"

# Параметры RSA ключа
KEY_SIZE = 4096  # Размер ключа в битах (безопасно для production)
PUBLIC_EXPONENT = 65537  # Стандартный публичный экспонент (F4)
KID = str(uuid.uuid4())  # Уникальный идентификатор ключа (Key ID)


def ensure_outdir(path: Path):
    """
    Создание директории для ключей если не существует.
    
    Args:
        path: Путь к директории
    """
    path.mkdir(parents=True, exist_ok=True)


def generate_rsa_key():
    """
    Генерация RSA приватного ключа.
    
    Returns:
        RSAPrivateKey: Сгенерированный приватный ключ
    """
    return rsa.generate_private_key(
        public_exponent=PUBLIC_EXPONENT,
        key_size=KEY_SIZE,
        backend=default_backend()
    )


def write_private_key(path: Path, key):
    """
    Сохранение приватного ключа в PEM формате.
    
    Ключ сохраняется в формате PKCS#8 без шифрования.
    Устанавливаются права доступа 0o600 (только владелец).
    
    Args:
        path: Путь к файлу
        key: Приватный ключ RSA
    """
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)
    
    # Устанавливаем права только для владельца
    try:
        path.chmod(0o600)
    except PermissionError:
        pass  # Игнорируем ошибку на Windows


def write_public_key(path: Path, key):
    """
    Сохранение публичного ключа в PEM формате.
    
    Args:
        path: Путь к файлу
        key: Приватный ключ (для извлечения публичного)
    """
    pub = key.public_key()
    pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    path.write_bytes(pem)


def int_to_base64url(n: int) -> str:
    """
    Конвертация целого числа в Base64URL формат.
    
    Используется для кодирования модуля (n) и экспоненты (e)
    в формате JWK.
    
    Args:
        n: Целое число для кодирования
        
    Returns:
        str: Строка в формате Base64URL без паддинга
    """
    length = (n.bit_length() + 7) // 8
    b = n.to_bytes(length, "big")
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def build_jwk_from_public_key(pubkey, kid: str, alg: str = "RS256", use: str = "sig"):
    """
    Создание JWK (JSON Web Key) из публичного ключа.
    
    JWK - это JSON представление криптографического ключа.
    Используется для передачи публичного ключа в OIDC/OAuth2 системах.
    
    Args:
        pubkey: Публичный ключ RSA
        kid: Key ID - уникальный идентификатор ключа
        alg: Алгоритм (по умолчанию RS256)
        use: Назначение ключа (sig = подпись)
        
    Returns:
        dict: JWK в виде словаря
    """
    numbers = pubkey.public_numbers()
    n_b64 = int_to_base64url(numbers.n)  # Модуль
    e_b64 = int_to_base64url(numbers.e)  # Публичный экспонент
    
    jwk = {
        "kty": "RSA",  # Key Type
        "use": use,    # Usage (sig = signature)
        "alg": alg,    # Algorithm
        "kid": kid,    # Key ID
        "n": n_b64,    # Modulus
        "e": e_b64,    # Exponent
    }
    return jwk


def save_json(path: Path, data):
    """
    Сохранение данных в JSON файл с форматированием.
    
    Args:
        path: Путь к файлу
        data: Данные для сохранения (dict или list)
    """
    path.write_text(json.dumps(data, indent=2))


def main():
    """
    Основная функция генерации ключей.
    
    Создаёт:
    1. RSA пару ключей (4096 бит)
    2. PEM файлы для приватного и публичного ключей
    3. JWK файл для публичного ключа
    4. JWKS файл (набор ключей) для OIDC
    """
    ensure_outdir(OUT_DIR)

    print("Generating RSA private key ({} bits)...".format(KEY_SIZE))
    key = generate_rsa_key()

    print("Writing private key to:", PRIVATE_KEY_FILE)
    write_private_key(PRIVATE_KEY_FILE, key)

    print("Writing public key to:", PUBLIC_KEY_FILE)
    write_public_key(PUBLIC_KEY_FILE, key)

    # Генерация JWK и JWKS
    pubkey = key.public_key()
    jwk = build_jwk_from_public_key(pubkey, kid=KID)
    jwks = {"keys": [jwk]}  # JWKS - это объект с массивом ключей

    print("Writing public JWK to:", PUBLIC_JWK_FILE)
    save_json(PUBLIC_JWK_FILE, jwk)

    print("Writing public JWKS to:", PUBLIC_JWKS_FILE)
    save_json(PUBLIC_JWKS_FILE, jwks)
    
    print("\nDone! Remember to:")
    print("1. Keep jwt_private_key.pem secret!")
    print("2. Update AUTH_JWT_SECRET_KEY in .env if using symmetric encryption")
    print("3. Configure your application to use the generated keys")


if __name__ == "__main__":
    main()
