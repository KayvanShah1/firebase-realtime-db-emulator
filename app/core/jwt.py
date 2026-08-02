from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.settings import settings
from app.schemas.token import TokenData

access_token_jwt_subject = "access"
password_reset_request_subject = "password_reset_token"

credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not verify token, token expired",
    headers={
        "WWW-AUTHENTICATE": "Bearer",
    },
)


def create_access_token(payload: dict, expires_delta=settings.access_token_expire_minutes):
    to_encode = payload.copy()
    expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
        )
        id: str = payload.get("id")
        if not id:
            raise credential_exception
        token_data = TokenData(id=id)
        return token_data
    except JWTError:
        raise credential_exception
