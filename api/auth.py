import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from fastapi import Request

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET is not set")
    return secret


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    valid_key = os.getenv("API_KEY_VALID")

    if not api_key or not valid_key or api_key != valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    return api_key


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        _jwt_secret(),
        algorithm=_jwt_algorithm(),
    )


def verify_jwt(token: str | None = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[_jwt_algorithm()],
        )
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def require_api_key_or_jwt(
    api_key: str | None = Security(api_key_header),
    token: str | None = Depends(oauth2_scheme),
) -> dict:
    valid_key = os.getenv("API_KEY_VALID")

    if api_key and valid_key and api_key == valid_key:
        return {"auth_type": "api_key"}

    if token:
        try:
            payload = jwt.decode(
                token,
                _jwt_secret(),
                algorithms=[_jwt_algorithm()],
            )
            return {"auth_type": "jwt", "payload": payload}
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )

def require_jwt_admin(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
) -> dict:
    if token:
        return verify_jwt(token)

    api_key = request.headers.get("X-API-Key")
    valid_key = os.getenv("API_KEY_VALID")

    if api_key and valid_key and api_key == valid_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT required for admin endpoint",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing bearer token",
    )