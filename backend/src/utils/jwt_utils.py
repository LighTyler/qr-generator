from datetime import UTC, datetime, timedelta


import jwt

from entrypoint.config import config


def encode_jwt(
        payload: dict,
        private_key: str = None,
        algorithm: str = None,
        expire_timedelta: timedelta | None = None,
        expire_minutes: int = None,
) -> str:

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
) -> dict:

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
