from cryptography.fernet import Fernet

import hashlib
import time
import uuid
import secrets

FERNET_KEY = Fernet.generate_key()
cipher = Fernet(FERNET_KEY)


def generate_token(username: str, id: int, email: str) -> tuple[str, str]:
    public_token = encrypt_public(f"{id}.{username}")
    private_token = hash_private_data(private=email)
    return private_token[0], f"{public_token}.{private_token}"

def check(username: str, id: int, email: str, recieved_token: str, salt: str):
    public_token = encrypt_public(f"{id}.{username}")
    private_token = hash_private_data(private=email, salt=salt)
    token = f"{public_token}.{private_token}"
    if recieved_token == token:
        return True
    return False

def decrypt_id(token: str):
    public_token = token.split(".")[0]
    decrypted_public_token = decrypt_public(public_token)
    try:
        user_id = int(decrypted_public_token[0])
        return user_id
    except:
        return None

def encrypt_public(public: str) -> str:
    public_token = cipher.encrypt(public.encode())
    return public_token.decode()


def decrypt_public(public: str) -> tuple:
    public_dec = cipher.decrypt(public.encode()).decode()
    return tuple(public_dec.split("."))

def hash_private_data(private: str, salt: str | None = None) -> tuple[str, str] | str:
    if salt is None:
        salt = f"{time.time()}{uuid.uuid4()}"
        private_token = f'{private}{salt}'
        return salt, hashlib.sha256(private_token.encode()).hexdigest()
    else:
        private_token = f'{private}{salt}'
        return hashlib.sha256(private_token.encode()).hexdigest()
