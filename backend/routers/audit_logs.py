from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from constants import UserRole
from database import get_db
from models import AuditLog, User
from security import require_roles


router = APIRouter()


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value)),
):
    query = db.query(AuditLog).order_by(AuditLog.id.desc())
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    data = [{
        "id": row.id,
        "actor_id": row.actor_id,
        "action": row.action,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "result": row.result,
        "detail": row.detail,
        "created_at": row.created_at,
    } for row in rows]
    return {"ok": True, "data": {"total": total, "rows": data}, "msg": ""}

