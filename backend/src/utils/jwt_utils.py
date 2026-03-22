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
):
    if private_key is None:
        private_key = config.auth_jwt.PRIVATE_KEY
    if algorithm is None:
        algorithm = config.auth_jwt.ALGORITM
    to_encode = payload.copy()
    now = datetime.now(UTC)

    if expire_timedelta:
        expire = now + expire_timedelta
    elif expire_minutes:
        expire = now + timedelta(minutes=expire_minutes)
    else:
        expire = now + timedelta(
            minutes=config.auth_jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    to_encode.update(
        exp=expire,
        iat=now,
    )
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
):
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
    return encode_jwt(
        payload=data,
        expire_minutes=expire_minutes,
    )


def create_refresh_token(data: dict) -> str:
    return encode_jwt(
        payload=data,
        expire_timedelta=timedelta(
            days=config.auth_jwt.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    )


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode("utf-8")


def validate_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password=password.encode(),
        hashed_password=hashed_password.encode("utf-8"),
    )
