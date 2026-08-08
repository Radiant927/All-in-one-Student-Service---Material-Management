from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from constants import BorrowApplicationStatus
from models import (
    BorrowApplication,
    InventoryBatch,
    InventoryItem,
    InventoryReservation,
    InventoryTransaction,
    Material,
    User,
)
from security import is_expired
from services.audit_service import add_audit_log
from services.inventory_service import borrow_material, return_material
from time_utils import utcnow


def application_data(application: BorrowApplication):
    return {
        "id": application.id,
        "applicant_id": application.applicant_id,
        "applicant_name": application.applicant.name if application.applicant else "",
        "student_no": application.applicant.student_no if application.applicant else None,
        "material_id": application.material_id,
        "material_name": application.material.name if application.material else "",
        "quantity": application.quantity,
        "item_code": application.item_code,
        "warehouse_id": application.warehouse_id,
        "status": application.status,
        "purpose": application.purpose,
        "review_note": application.review_note,
        "expires_at": application.expires_at,
        "picked_up_at": application.picked_up_at,
        "returned_at": application.returned_at,
        "created_at": application.created_at,
        "updated_at": application.updated_at,
    }


def release_reservation(application: BorrowApplication):
    reservation = application.reservation
    if reservation and reservation.active:
        reservation.active = False
        reservation.released_at = utcnow()


def expire_due_reservations(db: Session):
    reservations = db.query(InventoryReservation).filter(
        InventoryReservation.active.is_(True)
    ).all()
    changed = False
    for reservation in reservations:
        if is_expired(reservation.expires_at):
            reservation.active = False
            reservation.released_at = utcnow()
            if reservation.application.status == BorrowApplicationStatus.APPROVED.value:
                reservation.application.status = BorrowApplicationStatus.EXPIRED.value
                reservation.application.updated_at = utcnow()
            changed = True
    if changed:
        db.commit()


def material_available_quantity(db: Session, material: Material, exclude_application_id: int | None = None):
    reservation_query = db.query(func.sum(InventoryReservation.quantity)).filter(
        InventoryReservation.material_id == material.id,
        InventoryReservation.active.is_(True),
        InventoryReservation.expires_at > utcnow(),
    )
    if exclude_application_id is not None:
        reservation_query = reservation_query.filter(
            InventoryReservation.application_id != exclude_application_id
        )
    reserved = reservation_query.scalar() or 0
    if material.has_individual_tracking:
        physical = db.query(InventoryItem).filter(
            InventoryItem.material_id == material.id,
            InventoryItem.status == "available",
        ).count()
    else:
        physical = db.query(func.sum(InventoryBatch.quantity)).filter(
            InventoryBatch.material_id == material.id
        ).scalar() or 0
    return max(0, physical - reserved)


def approve_application(db: Session, application: BorrowApplication, actor: User, note: str, hours: int):
    if application.status != BorrowApplicationStatus.SUBMITTED.value:
        raise HTTPException(status_code=409, detail="只有待审核申请可以通过")
    material = db.query(Material).filter(Material.id == application.material_id).with_for_update().first()
    if material.has_individual_tracking:
        item = db.query(InventoryItem).filter(
            InventoryItem.material_id == material.id,
            InventoryItem.code == application.item_code,
        ).with_for_update().first()
        if not item or item.status != "available":
            raise HTTPException(status_code=409, detail="申请的个体物资当前不可用")
        conflict = db.query(InventoryReservation).filter(
            InventoryReservation.item_code == application.item_code,
            InventoryReservation.active.is_(True),
            InventoryReservation.expires_at > utcnow(),
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail="申请的个体物资已被预留")
    else:
        db.query(InventoryBatch).filter(
            InventoryBatch.material_id == material.id
        ).with_for_update().all()
        if material_available_quantity(db, material) < application.quantity:
            raise HTTPException(status_code=409, detail="可预留库存不足")

    expires_at = utcnow() + timedelta(hours=hours)
    reservation = InventoryReservation(
        application_id=application.id,
        material_id=application.material_id,
        item_code=application.item_code,
        quantity=application.quantity,
        expires_at=expires_at,
    )
    application.status = BorrowApplicationStatus.APPROVED.value
    application.approved_by = actor.id
    application.review_note = note
    application.expires_at = expires_at
    application.updated_at = utcnow()
    db.add(reservation)
    add_audit_log(db, actor, "borrow_application.approve", "borrow_application", application.id)
    db.commit()
    db.refresh(application)
    return application


def reject_application(db: Session, application: BorrowApplication, actor: User, note: str):
    if application.status != BorrowApplicationStatus.SUBMITTED.value:
        raise HTTPException(status_code=409, detail="只有待审核申请可以拒绝")
    application.status = BorrowApplicationStatus.REJECTED.value
    application.review_note = note
    application.approved_by = actor.id
    application.updated_at = utcnow()
    add_audit_log(db, actor, "borrow_application.reject", "borrow_application", application.id)
    db.commit()
    db.refresh(application)
    return application


def confirm_pickup(
    db: Session,
    application: BorrowApplication,
    actor: User,
    idempotency_key: str,
    warehouse_id: int | None,
):
    existing = db.query(InventoryTransaction).filter(
        InventoryTransaction.idempotency_key == idempotency_key
    ).first()
    if existing:
        if existing.application_id != application.id or existing.action != "borrow":
            raise HTTPException(status_code=409, detail="幂等键已用于其他操作")
        return application
    application = db.query(BorrowApplication).filter(
        BorrowApplication.id == application.id
    ).with_for_update().first()
    if application.status != BorrowApplicationStatus.APPROVED.value:
        raise HTTPException(status_code=409, detail="只有已通过申请可以确认领取")
    if application.expires_at and is_expired(application.expires_at):
        application.status = BorrowApplicationStatus.EXPIRED.value
        release_reservation(application)
        db.commit()
        raise HTTPException(status_code=409, detail="预留已过期")
    result = borrow_material(
        db,
        application.material_id,
        application.quantity,
        application.applicant.name,
        application.item_code,
        warehouse_id or application.warehouse_id,
        commit=False,
        reservation_application_id=application.id,
        actor_id=actor.id,
        record_transaction=False,
    )
    if not result.get("ok"):
        db.rollback()
        raise HTTPException(status_code=409, detail=result.get("msg", "领取失败"))
    application.status = BorrowApplicationStatus.PICKED_UP.value
    application.picked_up_at = utcnow()
    application.updated_at = utcnow()
    release_reservation(application)
    db.add(InventoryTransaction(
        application_id=application.id,
        material_id=application.material_id,
        warehouse_id=warehouse_id or application.warehouse_id,
        actor_id=actor.id,
        action="borrow",
        quantity=application.quantity,
        item_code=application.item_code,
        idempotency_key=idempotency_key,
    ))
    add_audit_log(db, actor, "borrow_application.confirm_pickup", "borrow_application", application.id)
    db.commit()
    db.refresh(application)
    return application


def confirm_return(
    db: Session,
    application: BorrowApplication,
    actor: User,
    idempotency_key: str,
    warehouse_id: int | None,
):
    existing = db.query(InventoryTransaction).filter(
        InventoryTransaction.idempotency_key == idempotency_key
    ).first()
    if existing:
        if existing.application_id != application.id or existing.action != "return":
            raise HTTPException(status_code=409, detail="幂等键已用于其他操作")
        return application
    application = db.query(BorrowApplication).filter(
        BorrowApplication.id == application.id
    ).with_for_update().first()
    if application.status != BorrowApplicationStatus.RETURN_PENDING.value:
        raise HTTPException(status_code=409, detail="只有待归还验收申请可以确认归还")
    result = return_material(
        db,
        application.material_id,
        application.quantity,
        application.applicant.name,
        application.item_code,
        warehouse_id or application.warehouse_id,
        commit=False,
        actor_id=actor.id,
        record_transaction=False,
    )
    if not result.get("ok"):
        db.rollback()
        raise HTTPException(status_code=409, detail=result.get("msg", "归还失败"))
    application.status = BorrowApplicationStatus.RETURNED.value
    application.returned_at = utcnow()
    application.updated_at = utcnow()
    db.add(InventoryTransaction(
        application_id=application.id,
        material_id=application.material_id,
        warehouse_id=warehouse_id or application.warehouse_id,
        actor_id=actor.id,
        action="return",
        quantity=application.quantity,
        item_code=application.item_code,
        idempotency_key=idempotency_key,
    ))
    add_audit_log(db, actor, "borrow_application.confirm_return", "borrow_application", application.id)
    db.commit()
    db.refresh(application)
    return application
