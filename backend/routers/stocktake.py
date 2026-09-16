import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from constants import UserRole
from database import get_db
from models import (
    AuditLog,
    InventoryBatch,
    InventoryItem,
    InventoryTransaction,
    Material,
    Stocktake,
    StocktakeEntry,
    StocktakeItemCheck,
    StorageLocation,
    User,
    Warehouse,
)
from schemas import StocktakeCreate, StocktakeEntryIn, StocktakeScanIn, StocktakeSurplusEntryCreate
from security import require_roles
from time_utils import utcnow_iso


router = APIRouter()
stocktake_roles = require_roles(UserRole.OPERATOR.value, UserRole.ADMIN.value)


def _active_stocktake(db: Session) -> Stocktake | None:
    return db.query(Stocktake).filter(Stocktake.status == "in_progress").first()


def _ensure_editable(db: Session, stocktake_id: int) -> Stocktake:
    stocktake = db.query(Stocktake).filter(Stocktake.id == stocktake_id).first()
    if not stocktake:
        raise HTTPException(status_code=404, detail="盘点单不存在")
    if stocktake.status != "in_progress":
        raise HTTPException(status_code=400, detail="盘点单已结束，无法修改")
    return stocktake


def _validate_location(db: Session, warehouse_id: int, location_id: int | None):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    if location_id is None:
        return
    location = db.query(StorageLocation).filter(StorageLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="储位不存在")
    if location.warehouse_id != warehouse_id:
        raise HTTPException(status_code=400, detail="储位不属于所选仓库")


def _bulk_quantity(db: Session, entry: StocktakeEntry, *, lock: bool = False) -> int:
    query = db.query(InventoryBatch).filter(
        InventoryBatch.material_id == entry.material_id,
        InventoryBatch.warehouse_id == entry.warehouse_id,
    )
    if entry.location_id is None:
        query = query.filter(InventoryBatch.location_id.is_(None))
    else:
        query = query.filter(InventoryBatch.location_id == entry.location_id)
    if lock:
        query = query.with_for_update()
    return sum(batch.quantity for batch in query.all())


def _entry_out(entry: StocktakeEntry):
    checks = sorted(entry.item_checks, key=lambda check: check.item_code)
    expected = [check for check in checks if check.expected]
    scanned = [check for check in checks if check.scanned]
    return {
        "id": entry.id,
        "material_id": entry.material_id,
        "material_name": entry.material.name if entry.material else "",
        "material_spec": entry.material.spec if entry.material else "",
        "is_individual": bool(entry.material and entry.material.has_individual_tracking),
        "warehouse_id": entry.warehouse_id,
        "warehouse_name": entry.warehouse.name if entry.warehouse else "",
        "location_id": entry.location_id,
        "location_code": entry.location.full_code if entry.location else "未指定储位",
        "book_quantity": entry.book_quantity,
        "actual_quantity": entry.actual_quantity,
        "difference": entry.difference,
        "counted": bool(entry.counted),
        "expected_count": len(expected),
        "scanned_count": len(scanned),
        "missing_codes": [check.item_code for check in expected if not check.scanned],
        "extra_codes": [check.item_code for check in scanned if not check.expected],
        "checks": [
            {
                "id": check.id,
                "item_code": check.item_code,
                "expected": bool(check.expected),
                "scanned": bool(check.scanned),
            }
            for check in checks
        ],
    }


def _stocktake_out(stocktake: Stocktake):
    entries = [_entry_out(entry) for entry in stocktake.entries]
    counted_entries = [entry for entry in stocktake.entries if entry.counted]
    return {
        "id": stocktake.id,
        "status": stocktake.status,
        "note": stocktake.note,
        "created_at": stocktake.created_at,
        "completed_at": stocktake.completed_at,
        "cancelled_at": stocktake.cancelled_at,
        "entries": entries,
        "entries_count": len(entries),
        "counted_count": len(counted_entries),
        "pending_count": len(entries) - len(counted_entries),
        "total_book": sum(entry.book_quantity for entry in stocktake.entries),
        "total_actual": sum(
            entry.actual_quantity for entry in counted_entries if entry.actual_quantity is not None
        ),
        "total_difference": sum(entry.difference for entry in counted_entries),
    }


@router.post("/stocktake")
def create_stocktake(
    body: StocktakeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    """按物资、仓库和储位创建账面快照；同一时间只允许一张进行中的盘点单。"""
    active = _active_stocktake(db)
    if active:
        raise HTTPException(status_code=409, detail=f"盘点单 #{active.id} 尚未结束")

    stocktake = Stocktake(status="in_progress", note=body.note.strip(), created_at=utcnow_iso())
    db.add(stocktake)
    db.flush()

    grouped_batches = defaultdict(int)
    for batch in db.query(InventoryBatch).filter(InventoryBatch.quantity > 0).all():
        grouped_batches[(batch.material_id, batch.warehouse_id, batch.location_id)] += batch.quantity
    for (material_id, warehouse_id, location_id), quantity in grouped_batches.items():
        db.add(StocktakeEntry(
            stocktake_id=stocktake.id,
            material_id=material_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            book_quantity=quantity,
            actual_quantity=None,
            difference=0,
            counted=False,
        ))

    grouped_items = defaultdict(list)
    available_items = db.query(InventoryItem).filter(InventoryItem.status == "available").all()
    for item in available_items:
        grouped_items[(item.material_id, item.warehouse_id, item.location_id)].append(item)
    for (material_id, warehouse_id, location_id), items in grouped_items.items():
        entry = StocktakeEntry(
            stocktake_id=stocktake.id,
            material_id=material_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            book_quantity=len(items),
            actual_quantity=0,
            difference=-len(items),
            counted=False,
        )
        db.add(entry)
        db.flush()
        for item in items:
            db.add(StocktakeItemCheck(
                stocktake_entry_id=entry.id,
                inventory_item_id=item.id,
                item_code=item.code,
                expected=True,
                scanned=False,
            ))

    db.flush()
    entry_count = len(stocktake.entries)
    db.add(AuditLog(
        actor_id=current_user.id,
        action="stocktake.create",
        target_type="stocktake",
        target_id=str(stocktake.id),
        result="success",
        detail=json.dumps({"entries": entry_count}, ensure_ascii=False),
    ))
    db.commit()
    return {
        "ok": True,
        "data": {"id": stocktake.id, "entries": entry_count},
        "msg": f"创建盘点单成功，共 {entry_count} 条待盘点项",
    }


@router.get("/stocktake")
def list_stocktakes(
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    items = db.query(Stocktake).order_by(Stocktake.id.desc()).all()
    data = []
    for stocktake in items:
        data.append({
            "id": stocktake.id,
            "status": stocktake.status,
            "note": stocktake.note,
            "created_at": stocktake.created_at,
            "completed_at": stocktake.completed_at,
            "cancelled_at": stocktake.cancelled_at,
            "entries_count": len(stocktake.entries),
            "counted_count": sum(1 for entry in stocktake.entries if entry.counted),
            "discrepancy_count": sum(
                1 for entry in stocktake.entries if entry.counted and entry.difference != 0
            ),
        })
    return {"ok": True, "data": data, "msg": ""}


@router.get("/stocktake/{stocktake_id}")
def get_stocktake(
    stocktake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    stocktake = db.query(Stocktake).filter(Stocktake.id == stocktake_id).first()
    if not stocktake:
        raise HTTPException(status_code=404, detail="盘点单不存在")
    return {"ok": True, "data": _stocktake_out(stocktake), "msg": ""}


@router.put("/stocktake/{stocktake_id}/entry/{entry_id}")
def update_entry(
    stocktake_id: int,
    entry_id: int,
    body: StocktakeEntryIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    _ensure_editable(db, stocktake_id)
    entry = db.query(StocktakeEntry).filter(
        StocktakeEntry.id == entry_id,
        StocktakeEntry.stocktake_id == stocktake_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="盘点明细不存在")
    if entry.material and entry.material.has_individual_tracking:
        raise HTTPException(status_code=400, detail="个体追踪物资必须逐个扫码盘点")
    entry.actual_quantity = body.actual_quantity
    entry.difference = body.actual_quantity - entry.book_quantity
    entry.counted = True
    db.commit()
    return {"ok": True, "data": _entry_out(entry), "msg": "清点数量已更新"}


@router.post("/stocktake/{stocktake_id}/entries")
def add_surplus_entry(
    stocktake_id: int,
    body: StocktakeSurplusEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    _ensure_editable(db, stocktake_id)
    material = db.query(Material).filter(Material.id == body.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物资不存在")
    _validate_location(db, body.warehouse_id, body.location_id)
    duplicate = db.query(StocktakeEntry).filter(
        StocktakeEntry.stocktake_id == stocktake_id,
        StocktakeEntry.material_id == body.material_id,
        StocktakeEntry.warehouse_id == body.warehouse_id,
        StocktakeEntry.location_id == body.location_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="该物资、仓库和储位已在盘点单中")

    probe = StocktakeEntry(
        material_id=body.material_id,
        warehouse_id=body.warehouse_id,
        location_id=body.location_id,
    )
    if not material.has_individual_tracking and _bulk_quantity(db, probe) != 0:
        raise HTTPException(status_code=409, detail="该位置已有账面库存，请刷新盘点单")
    entry = StocktakeEntry(
        stocktake_id=stocktake_id,
        material_id=body.material_id,
        warehouse_id=body.warehouse_id,
        location_id=body.location_id,
        book_quantity=0,
        actual_quantity=0 if material.has_individual_tracking else body.actual_quantity,
        difference=0 if material.has_individual_tracking else body.actual_quantity,
        counted=False if material.has_individual_tracking else True,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"ok": True, "data": _entry_out(entry), "msg": "盘盈项已加入盘点单"}


def _scan_code(payload: str) -> str:
    value = payload.strip()
    if value.startswith("ITEM:"):
        value = value.split(":", 1)[1]
    elif value.startswith("MATERIAL:ac-remote:"):
        value = value.split(":", 2)[2]
    value = value.strip()
    if not value:
        raise HTTPException(status_code=422, detail="个体编号不能为空")
    return value


@router.post("/stocktake/{stocktake_id}/entry/{entry_id}/scan")
def scan_entry_item(
    stocktake_id: int,
    entry_id: int,
    body: StocktakeScanIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    _ensure_editable(db, stocktake_id)
    entry = db.query(StocktakeEntry).filter(
        StocktakeEntry.id == entry_id,
        StocktakeEntry.stocktake_id == stocktake_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="盘点明细不存在")
    if not entry.material or not entry.material.has_individual_tracking:
        raise HTTPException(status_code=400, detail="该盘点项不是个体追踪物资")

    code = _scan_code(body.payload)
    item = db.query(InventoryItem).filter(InventoryItem.code == code).first()
    if item and item.material_id != entry.material_id:
        raise HTTPException(status_code=409, detail="该编号属于其他物资")
    if item and item.status == "borrowed":
        raise HTTPException(status_code=409, detail="该编号处于借出状态，请先办理归还")
    already_scanned = db.query(StocktakeItemCheck).join(StocktakeEntry).filter(
        StocktakeEntry.stocktake_id == stocktake_id,
        StocktakeItemCheck.item_code == code,
        StocktakeItemCheck.scanned.is_(True),
        StocktakeItemCheck.stocktake_entry_id != entry_id,
    ).first()
    if already_scanned:
        raise HTTPException(status_code=409, detail="该编号已在其他盘点位置扫描")

    check = db.query(StocktakeItemCheck).filter(
        StocktakeItemCheck.stocktake_entry_id == entry_id,
        StocktakeItemCheck.item_code == code,
    ).first()
    if check and check.scanned:
        raise HTTPException(status_code=409, detail="该编号已扫描，请勿重复录入")
    if check:
        check.scanned = True
        check.scanned_at = utcnow_iso()
    else:
        check = StocktakeItemCheck(
            stocktake_entry_id=entry_id,
            inventory_item_id=item.id if item else None,
            item_code=code,
            expected=False,
            scanned=True,
            scanned_at=utcnow_iso(),
        )
        db.add(check)
    db.flush()
    scanned_count = db.query(StocktakeItemCheck).filter(
        StocktakeItemCheck.stocktake_entry_id == entry.id,
        StocktakeItemCheck.scanned.is_(True),
    ).count()
    entry.actual_quantity = scanned_count
    entry.difference = scanned_count - entry.book_quantity
    entry.counted = False
    db.commit()
    return {"ok": True, "data": _entry_out(entry), "msg": f"已扫描 {code}"}


@router.delete("/stocktake/{stocktake_id}/entry/{entry_id}/scan/{check_id}")
def undo_entry_scan(
    stocktake_id: int,
    entry_id: int,
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    _ensure_editable(db, stocktake_id)
    entry = db.query(StocktakeEntry).filter(
        StocktakeEntry.id == entry_id,
        StocktakeEntry.stocktake_id == stocktake_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="盘点明细不存在")
    check = db.query(StocktakeItemCheck).filter(
        StocktakeItemCheck.id == check_id,
        StocktakeItemCheck.stocktake_entry_id == entry_id,
    ).first()
    if not check or not check.scanned:
        raise HTTPException(status_code=404, detail="扫码记录不存在")
    if check.expected:
        check.scanned = False
        check.scanned_at = None
    else:
        db.delete(check)
    db.flush()
    scanned_count = db.query(StocktakeItemCheck).filter(
        StocktakeItemCheck.stocktake_entry_id == entry.id,
        StocktakeItemCheck.scanned.is_(True),
    ).count()
    entry.actual_quantity = scanned_count
    entry.difference = scanned_count - entry.book_quantity
    entry.counted = False
    db.commit()
    return {"ok": True, "data": _entry_out(entry), "msg": "已撤销扫码"}


@router.post("/stocktake/{stocktake_id}/entry/{entry_id}/confirm")
def confirm_entry(
    stocktake_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    _ensure_editable(db, stocktake_id)
    entry = db.query(StocktakeEntry).filter(
        StocktakeEntry.id == entry_id,
        StocktakeEntry.stocktake_id == stocktake_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="盘点明细不存在")
    if not entry.material or not entry.material.has_individual_tracking:
        raise HTTPException(status_code=400, detail="普通物资录入实际数量后会自动确认")
    scanned_count = sum(1 for check in entry.item_checks if check.scanned)
    entry.actual_quantity = scanned_count
    entry.difference = scanned_count - entry.book_quantity
    entry.counted = True
    db.commit()
    return {"ok": True, "data": _entry_out(entry), "msg": "该储位已确认清点完成"}


def _snapshot_conflicts(db: Session, stocktake: Stocktake) -> list[str]:
    conflicts = []
    for entry in stocktake.entries:
        if entry.material and entry.material.has_individual_tracking:
            for check in entry.item_checks:
                if not check.expected or not check.inventory_item_id:
                    continue
                item = db.query(InventoryItem).filter(
                    InventoryItem.id == check.inventory_item_id
                ).with_for_update().first()
                if (
                    not item
                    or item.status != "available"
                    or item.warehouse_id != entry.warehouse_id
                    or item.location_id != entry.location_id
                ):
                    conflicts.append(f"{entry.material.name}/{check.item_code}")
        elif _bulk_quantity(db, entry, lock=True) != entry.book_quantity:
            location = entry.location.full_code if entry.location else "未指定"
            conflicts.append(f"{entry.material.name}/{entry.warehouse.name}/{location}")
    return conflicts


@router.post("/stocktake/{stocktake_id}/complete")
def complete_stocktake(
    stocktake_id: int,
    apply_fix: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    stocktake = _ensure_editable(db, stocktake_id)
    pending = [entry for entry in stocktake.entries if not entry.counted]
    if pending:
        raise HTTPException(status_code=409, detail=f"还有 {len(pending)} 项未确认清点")

    if apply_fix:
        conflicts = _snapshot_conflicts(db, stocktake)
        if conflicts:
            preview = "、".join(conflicts[:3])
            raise HTTPException(status_code=409, detail=f"盘点期间库存已变化：{preview}，请取消后重新盘点")

    changes = []
    if apply_fix:
        scanned_codes = {
            check.item_code
            for entry in stocktake.entries
            for check in entry.item_checks
            if check.scanned
        }
        for entry in stocktake.entries:
            material = entry.material
            actual = entry.actual_quantity or 0
            if material.has_individual_tracking:
                for check in entry.item_checks:
                    if (
                        check.expected
                        and not check.scanned
                        and check.item_code not in scanned_codes
                        and check.inventory_item
                    ):
                        check.inventory_item.status = "missing"
                        db.add(InventoryTransaction(
                            material_id=entry.material_id,
                            warehouse_id=entry.warehouse_id,
                            actor_id=current_user.id,
                            action="stocktake_adjust",
                            quantity=-1,
                            item_code=check.item_code,
                        ))
                        changes.append(f"{check.item_code}: 标记缺失")
                    elif check.scanned:
                        item = check.inventory_item
                        if item is None:
                            item = InventoryItem(
                                material_id=entry.material_id,
                                code=check.item_code,
                                status="available",
                                warehouse_id=entry.warehouse_id,
                                location_id=entry.location_id,
                                created_at=utcnow_iso(),
                            )
                            db.add(item)
                            db.flush()
                            check.inventory_item_id = item.id
                            db.add(InventoryTransaction(
                                material_id=entry.material_id,
                                warehouse_id=entry.warehouse_id,
                                actor_id=current_user.id,
                                action="stocktake_adjust",
                                quantity=1,
                                item_code=check.item_code,
                            ))
                            changes.append(f"{check.item_code}: 补录")
                        else:
                            moved = item.warehouse_id != entry.warehouse_id or item.location_id != entry.location_id
                            recovered = item.status == "missing"
                            item.status = "available"
                            item.warehouse_id = entry.warehouse_id
                            item.location_id = entry.location_id
                            if moved or recovered:
                                db.add(InventoryTransaction(
                                    material_id=entry.material_id,
                                    warehouse_id=entry.warehouse_id,
                                    actor_id=current_user.id,
                                    action="stocktake_adjust",
                                    quantity=1 if recovered else 0,
                                    item_code=check.item_code,
                                ))
                                changes.append(f"{check.item_code}: {'找回' if recovered else '修正位置'}")
            elif entry.difference != 0:
                query = db.query(InventoryBatch).filter(
                    InventoryBatch.material_id == entry.material_id,
                    InventoryBatch.warehouse_id == entry.warehouse_id,
                )
                if entry.location_id is None:
                    query = query.filter(InventoryBatch.location_id.is_(None))
                else:
                    query = query.filter(InventoryBatch.location_id == entry.location_id)
                batches = query.with_for_update().all()
                if batches:
                    batches[0].quantity = actual
                    batches[0].updated_at = utcnow_iso()
                    for duplicate in batches[1:]:
                        duplicate.quantity = 0
                        duplicate.updated_at = utcnow_iso()
                else:
                    db.add(InventoryBatch(
                        material_id=entry.material_id,
                        warehouse_id=entry.warehouse_id,
                        location_id=entry.location_id,
                        quantity=actual,
                        created_at=utcnow_iso(),
                        updated_at=utcnow_iso(),
                    ))
                db.add(InventoryTransaction(
                    material_id=entry.material_id,
                    warehouse_id=entry.warehouse_id,
                    actor_id=current_user.id,
                    action="stocktake_adjust",
                    quantity=entry.difference,
                ))
                changes.append(f"{material.name}: {entry.book_quantity}->{actual}")

    stocktake.status = "completed"
    stocktake.completed_at = utcnow_iso()
    db.add(AuditLog(
        actor_id=current_user.id,
        action="stocktake.complete_and_fix" if apply_fix else "stocktake.complete",
        target_type="stocktake",
        target_id=str(stocktake.id),
        result="success",
        detail=json.dumps({"changes": changes}, ensure_ascii=False),
    ))
    db.commit()
    message = "盘点完成"
    if apply_fix:
        message += f"，已记录 {len(changes)} 项修正"
    return {"ok": True, "data": {"fixed": changes}, "msg": message}


@router.post("/stocktake/{stocktake_id}/cancel")
def cancel_stocktake(
    stocktake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(stocktake_roles),
):
    stocktake = _ensure_editable(db, stocktake_id)
    stocktake.status = "cancelled"
    stocktake.cancelled_at = utcnow_iso()
    db.add(AuditLog(
        actor_id=current_user.id,
        action="stocktake.cancel",
        target_type="stocktake",
        target_id=str(stocktake.id),
        result="success",
        detail="",
    ))
    db.commit()
    return {"ok": True, "data": None, "msg": "盘点单已取消"}
