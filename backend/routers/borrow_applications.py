from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from constants import BorrowApplicationStatus, UserRole
from database import get_db
from models import BorrowApplication, InventoryItem, Material, User
from schemas import BorrowApplicationAction, BorrowApplicationCreate, BorrowApplicationReview
from security import get_current_user, require_roles
from services.audit_service import add_audit_log
from services.borrow_application_service import (
    application_data,
    approve_application,
    confirm_pickup,
    confirm_return,
    expire_due_reservations,
    reject_application,
    release_reservation,
)
from time_utils import utcnow


router = APIRouter()


def _get_application(db: Session, application_id: int):
    application = db.query(BorrowApplication).filter(BorrowApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="借用申请不存在")
    return application


@router.post("/borrow-applications")
def create_application(
    body: BorrowApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = db.query(Material).filter(Material.id == body.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物资不存在")
    item_code = body.item_code.strip() if body.item_code else None
    if material.has_individual_tracking:
        if not item_code or body.quantity != 1:
            raise HTTPException(status_code=422, detail="个体物资必须选择代号且数量为1")
        item = db.query(InventoryItem).filter(
            InventoryItem.material_id == material.id,
            InventoryItem.code == item_code,
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="个体物资代号不存在")
    application = BorrowApplication(
        applicant_id=current_user.id,
        material_id=material.id,
        quantity=body.quantity,
        item_code=item_code,
        warehouse_id=body.warehouse_id,
        purpose=body.purpose.strip(),
        status=BorrowApplicationStatus.SUBMITTED.value,
    )
    db.add(application)
    db.flush()
    add_audit_log(db, current_user, "borrow_application.create", "borrow_application", application.id)
    db.commit()
    db.refresh(application)
    return {"ok": True, "data": application_data(application), "msg": "借用申请已提交"}


@router.get("/borrow-applications/mine")
def list_my_applications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expire_due_reservations(db)
    query = db.query(BorrowApplication).filter(
        BorrowApplication.applicant_id == current_user.id
    ).order_by(BorrowApplication.id.desc())
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    return {"ok": True, "data": {"total": total, "rows": [application_data(x) for x in rows]}, "msg": ""}


@router.get("/borrow-applications")
def list_applications(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR.value, UserRole.ADMIN.value)),
):
    expire_due_reservations(db)
    query = db.query(BorrowApplication).order_by(BorrowApplication.id.desc())
    if status:
        query = query.filter(BorrowApplication.status == status)
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    return {"ok": True, "data": {"total": total, "rows": [application_data(x) for x in rows]}, "msg": ""}


@router.post("/borrow-applications/{application_id}/approve")
def approve(
    application_id: int,
    body: BorrowApplicationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR.value, UserRole.ADMIN.value)),
):
    application = approve_application(db, _get_application(db, application_id), current_user, body.note, body.reservation_hours)
    return {"ok": True, "data": application_data(application), "msg": "申请已通过并预留库存"}


@router.post("/borrow-applications/{application_id}/reject")
def reject(
    application_id: int,
    body: BorrowApplicationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR.value, UserRole.ADMIN.value)),
):
    application = reject_application(db, _get_application(db, application_id), current_user, body.note)
    return {"ok": True, "data": application_data(application), "msg": "申请已拒绝"}


@router.post("/borrow-applications/{application_id}/cancel")
def cancel(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = _get_application(db, application_id)
    if application.applicant_id != current_user.id and current_user.role not in {
        UserRole.OPERATOR.value, UserRole.ADMIN.value
    }:
        raise HTTPException(status_code=403, detail="只能取消自己的申请")
    if application.status not in {
        BorrowApplicationStatus.SUBMITTED.value,
        BorrowApplicationStatus.APPROVED.value,
    }:
        raise HTTPException(status_code=409, detail="当前状态不能取消")
    release_reservation(application)
    application.status = BorrowApplicationStatus.CANCELLED.value
    application.updated_at = utcnow()
    add_audit_log(db, current_user, "borrow_application.cancel", "borrow_application", application.id)
    db.commit()
    db.refresh(application)
    return {"ok": True, "data": application_data(application), "msg": "申请已取消"}


@router.post("/borrow-applications/{application_id}/confirm-pickup")
def pickup(
    application_id: int,
    body: BorrowApplicationAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR.value, UserRole.ADMIN.value)),
):
    application = confirm_pickup(db, _get_application(db, application_id), current_user, body.idempotency_key, body.warehouse_id)
    return {"ok": True, "data": application_data(application), "msg": "领取已确认，库存已扣减"}


@router.post("/borrow-applications/{application_id}/request-return")
def request_return(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = _get_application(db, application_id)
    if application.applicant_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能归还自己的借用物资")
    if application.status != BorrowApplicationStatus.PICKED_UP.value:
        raise HTTPException(status_code=409, detail="只有已领取申请可以发起归还")
    application.status = BorrowApplicationStatus.RETURN_PENDING.value
    application.updated_at = utcnow()
    add_audit_log(db, current_user, "borrow_application.request_return", "borrow_application", application.id)
    db.commit()
    db.refresh(application)
    return {"ok": True, "data": application_data(application), "msg": "归还申请已提交，请等待验收"}


@router.post("/borrow-applications/{application_id}/confirm-return")
def return_confirm(
    application_id: int,
    body: BorrowApplicationAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR.value, UserRole.ADMIN.value)),
):
    application = confirm_return(db, _get_application(db, application_id), current_user, body.idempotency_key, body.warehouse_id)
    return {"ok": True, "data": application_data(application), "msg": "归还验收完成，库存已恢复"}

