import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings


class AuthService:
    SECRET_KEY: str = settings.SECRET_KEY
    ALGORITHM: str = settings.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS: int = settings.REFRESH_TOKEN_EXPIRE_DAYS

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except ValueError:
            return False

    @classmethod
    def create_access_token(
        cls,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (
            expires_delta
            if expires_delta is not None
            else timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.setdefault("type", "access")
        to_encode.update({"exp": expire, "iat": now})
        return jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def create_refresh_token(cls) -> str:
        """Generate a cryptographically secure random refresh token."""
        return secrets.token_urlsafe(48)

    @classmethod
    def hash_token(cls, token: str) -> str:
        """Hash a token with SHA-256 for secure indexed storage."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(
                token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM]
            )
            return payload
        except JWTError:
            return None
