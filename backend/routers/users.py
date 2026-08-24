from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from constants import UserRole, UserStatus
from database import get_db
from models import User
from schemas import UserUpdate
from security import require_roles
from services.audit_service import add_audit_log


router = APIRouter()


def _user_data(user: User):
    return {
        "id": user.id,
        "external_subject": user.external_subject,
        "student_no": user.student_no,
        "name": user.name,
        "role": user.role,
        "status": user.status,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.get("/users")
def list_users(
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value)),
):
    query = db.query(User).order_by(User.id.desc())
    if search:
        value = f"%{search.strip()}%"
        query = query.filter((User.name.like(value)) | (User.student_no.like(value)))
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    return {"ok": True, "data": {"total": total, "rows": [_user_data(x) for x in rows]}, "msg": ""}


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_user.id and (
        (body.role and body.role != UserRole.ADMIN.value)
        or body.status == UserStatus.DISABLED.value
    ):
        raise HTTPException(status_code=409, detail="不能降低或停用当前管理员账号")
    if body.role is not None:
        if body.role not in {role.value for role in UserRole}:
            raise HTTPException(status_code=422, detail="无效用户角色")
        user.role = body.role
    if body.status is not None:
        if body.status not in {status.value for status in UserStatus}:
            raise HTTPException(status_code=422, detail="无效用户状态")
        user.status = body.status
    add_audit_log(
        db,
        current_user,
        "user.update",
        "user",
        user.id,
        detail={"role": user.role, "status": user.status},
    )
    db.commit()
    db.refresh(user)
    return {"ok": True, "data": _user_data(user), "msg": "用户权限已更新"}

