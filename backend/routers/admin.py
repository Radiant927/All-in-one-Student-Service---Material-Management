from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import AdminVerify, AdminChangePassword, ApiResponse

router = APIRouter()


@router.post("/admin/verify")
def verify(body: AdminVerify, db: Session = Depends(get_db)):
    from models import AdminSetting
    setting = db.query(AdminSetting).filter(AdminSetting.key == "password").first()
    if not setting:
        return {"ok": False, "data": None, "msg": "系统未初始化"}
    if setting.value == body.password:
        return {"ok": True, "data": None, "msg": "验证成功"}
    return {"ok": False, "data": None, "msg": "密码错误"}


@router.put("/admin/password")
def change_password(body: AdminChangePassword, db: Session = Depends(get_db)):
    from models import AdminSetting
    setting = db.query(AdminSetting).filter(AdminSetting.key == "password").first()
    if not setting:
        return {"ok": False, "data": None, "msg": "系统未初始化"}
    if setting.value != body.old_password:
        return {"ok": False, "data": None, "msg": "原密码错误"}
    setting.value = body.new_password
    db.commit()
    return {"ok": True, "data": None, "msg": "密码修改成功"}