from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import AdminVerify, AdminChangePassword, ApiResponse
from pydantic import BaseModel
from typing import Optional
import hashlib
import secrets

router = APIRouter()


def hash_password(password: str) -> str:
    """Hash a password with SHA-256 + random salt. Returns 'hash:salt'."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{password}:{salt}".encode()).hexdigest()
    return f"{h}:{salt}"


def verify_password_hash(password: str, stored: str) -> bool:
    """Verify a password against a stored value (supports old plaintext and new 'hash:salt').
    Returns (is_valid: bool, needs_upgrade: bool)."""
    if ":" not in stored:
        # Old plaintext password — accept but mark for upgrade
        return password == stored
    try:
        h, salt = stored.split(":", 1)
        expected = hashlib.sha256(f"{password}:{salt}".encode()).hexdigest()
        return h == expected
    except (ValueError, AttributeError):
        return False


class TestEmailRequest(BaseModel):
    email: str


@router.post("/admin/verify")
def verify(body: AdminVerify, db: Session = Depends(get_db)):
    from models import AdminSetting
    setting = db.query(AdminSetting).filter(AdminSetting.key == "password").first()
    if not setting:
        return {"ok": False, "data": None, "msg": "系统未初始化"}
    if verify_password_hash(body.password, setting.value):
        return {"ok": True, "data": None, "msg": "验证成功"}
    return {"ok": False, "data": None, "msg": "密码错误"}


@router.put("/admin/password")
def change_password(body: AdminChangePassword, db: Session = Depends(get_db)):
    from models import AdminSetting
    setting = db.query(AdminSetting).filter(AdminSetting.key == "password").first()
    if not setting:
        return {"ok": False, "data": None, "msg": "系统未初始化"}
    if not verify_password_hash(body.old_password, setting.value):
        return {"ok": False, "data": None, "msg": "原密码错误"}
    if len(body.new_password) < 4:
        return {"ok": False, "data": None, "msg": "新密码至少需要4个字符"}
    setting.value = hash_password(body.new_password)
    db.commit()
    return {"ok": True, "data": None, "msg": "密码修改成功"}


@router.get("/admin/settings")
def list_settings(db: Session = Depends(get_db)):
    """Get all non-sensitive admin settings."""
    from models import AdminSetting
    # smtp_pass 不可通过 API 读取，仅可写入
    READ_BLOCKED = {"password", "smtp_pass"}
    settings = db.query(AdminSetting).filter(
        AdminSetting.key.notin_(READ_BLOCKED)
    ).all()
    data = {s.key: s.value for s in settings}
    return {"ok": True, "data": data, "msg": ""}


@router.put("/admin/settings")
def update_settings(body: dict, db: Session = Depends(get_db)):
    """Batch update admin settings (key-value pairs). Sensitive keys like 'password' are filtered."""
    from models import AdminSetting
    SENSITIVE_KEYS = {"password", "smtp_pass", "smtp_user"}
    for key, value in body.items():
        if key in SENSITIVE_KEYS:
            continue
        setting = db.query(AdminSetting).filter(AdminSetting.key == key).first()
        if setting:
            setting.value = str(value) if value is not None else ""
        else:
            db.add(AdminSetting(key=key, value=str(value) if value is not None else ""))
    db.commit()
    return {"ok": True, "data": None, "msg": "设置已保存"}


@router.post("/admin/test-email")
def test_email(body: TestEmailRequest, db: Session = Depends(get_db)):
    """Send a test email to verify SMTP configuration."""
    from services.email_service import send_test_email
    result = send_test_email(db, body.email)
    return result