import json
from sqlalchemy.orm import Session

from models import AuditLog, User


def add_audit_log(
    db: Session,
    actor: User | None,
    action: str,
    target_type: str,
    target_id=None,
    result: str = "success",
    detail=None,
):
    if isinstance(detail, (dict, list)):
        detail = json.dumps(detail, ensure_ascii=False, default=str)
    db.add(AuditLog(
        actor_id=actor.id if actor else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        result=result,
        detail=detail or "",
    ))

