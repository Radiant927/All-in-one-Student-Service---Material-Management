import hashlib
import os
import secrets
from datetime import timedelta, timezone
from typing import Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from constants import UserStatus
from database import get_db
from models import RefreshToken, User
from time_utils import utcnow


bearer_scheme = HTTPBearer(auto_error=False)


def _jwt_secret() -> str:
    value = os.getenv("JWT_SECRET", "development-only-secret-change-me")
    if os.getenv("APP_ENV", "development").lower() == "production" and value == "development-only-secret-change-me":
        raise RuntimeError("生产环境必须配置 JWT_SECRET")
    return value


def access_token_minutes() -> int:
    return max(5, int(os.getenv("ACCESS_TOKEN_MINUTES", "30")))


def refresh_token_days() -> int:
    return max(1, int(os.getenv("REFRESH_TOKEN_DAYS", "14")))


def create_access_token(user: User) -> tuple[str, int]:
    minutes = access_token_minutes()
    now = utcnow()
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256"), minutes * 60


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(48)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=utcnow() + timedelta(days=refresh_token_days()),
    ))
    return raw_token


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="令牌类型错误")
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="登录已过期") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="无效登录令牌") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="请先登录")
    payload = decode_access_token(credentials.credentials)
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="用户不存在或已停用")
    return user


def require_roles(*roles: str) -> Callable:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="没有执行此操作的权限")
        return current_user
    return dependency


def is_expired(value) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= utcnow()

