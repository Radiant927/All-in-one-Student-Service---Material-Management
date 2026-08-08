from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth_providers import get_auth_provider
from constants import UserStatus
from database import get_db
from models import RefreshToken, User
from schemas import AuthLoginRequest, LogoutRequest, RefreshTokenRequest
from security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_refresh_token,
    is_expired,
)
from services.audit_service import add_audit_log
from time_utils import utcnow


router = APIRouter()


def _user_data(user: User):
    return {
        "id": user.id,
        "external_subject": user.external_subject,
        "student_no": user.student_no,
        "name": user.name,
        "role": user.role,
        "status": user.status,
    }


def issue_token_pair(db: Session, user: User):
    access_token, expires_in = create_access_token(user)
    refresh_token = create_refresh_token(db, user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": _user_data(user),
    }


@router.post("/auth/login")
def login(body: AuthLoginRequest, db: Session = Depends(get_db)):
    identity = get_auth_provider().authenticate(body)
    user = db.query(User).filter(User.external_subject == identity.external_subject).first()
    if not user:
        user = User(
            external_subject=identity.external_subject,
            student_no=identity.student_no,
            name=identity.name,
            role=identity.role,
            status=UserStatus.ACTIVE.value,
        )
        db.add(user)
        db.flush()
    else:
        user.name = identity.name or user.name
        user.student_no = identity.student_no or user.student_no
    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=403, detail="账号已停用")
    data = issue_token_pair(db, user)
    add_audit_log(db, user, "auth.login", "user", user.id)
    db.commit()
    return {"ok": True, "data": data, "msg": "登录成功"}


@router.post("/auth/refresh")
def refresh(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_refresh_token(body.refresh_token),
        RefreshToken.revoked_at.is_(None),
    ).first()
    if not record or is_expired(record.expires_at):
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="用户不存在或已停用")
    record.revoked_at = utcnow()
    data = issue_token_pair(db, user)
    db.commit()
    return {"ok": True, "data": data, "msg": "令牌已刷新"}


@router.post("/auth/logout")
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_refresh_token(body.refresh_token)
    ).first()
    if record and record.revoked_at is None:
        record.revoked_at = utcnow()
        db.commit()
    return {"ok": True, "data": None, "msg": "已退出登录"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"ok": True, "data": _user_data(current_user), "msg": ""}

