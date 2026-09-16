from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Material, InventoryItem, InventoryBatch, BorrowHistory, InventoryTransaction, Warehouse, StorageLocation
from time_utils import utcnow, utcnow_iso


def get_material_inventory_summary(db: Session, material_id: int):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return {"total_quantity": 0, "borrowed_quantity": 0, "available_quantity": 0}

    if m.has_individual_tracking:
        total = db.query(InventoryItem).filter(InventoryItem.material_id == material_id).count()
        borrowed = db.query(InventoryItem).filter(
            InventoryItem.material_id == material_id,
            InventoryItem.status == "borrowed"
        ).count()
        available = db.query(InventoryItem).filter(
            InventoryItem.material_id == material_id,
            InventoryItem.status == "available"
        ).count()
    else:
        total = db.query(func.sum(InventoryBatch.quantity)).filter(
            InventoryBatch.material_id == material_id
        ).scalar() or 0
        total_borrowed = db.query(func.sum(BorrowHistory.quantity)).filter(
            BorrowHistory.material_id == material_id,
            BorrowHistory.action == "borrow"
        ).scalar() or 0
        total_returned = db.query(func.sum(BorrowHistory.quantity)).filter(
            BorrowHistory.material_id == material_id,
            BorrowHistory.action == "return"
        ).scalar() or 0
        borrowed = total_borrowed - total_returned
        available = total

    return {
        "total_quantity": total,
        "borrowed_quantity": borrowed,
        "available_quantity": available
    }


def get_inventory_batches(db: Session, material_id: int):
    batches = db.query(InventoryBatch).filter(InventoryBatch.material_id == material_id).all()
    result = []
    for b in batches:
        wh = db.query(Warehouse).filter(Warehouse.id == b.warehouse_id).first()
        loc = db.query(StorageLocation).filter(StorageLocation.id == b.location_id).first() if b.location_id else None
        result.append({
            "id": b.id, "material_id": b.material_id, "warehouse_id": b.warehouse_id,
            "location_id": b.location_id, "quantity": b.quantity,
            "warehouse_name": wh.name if wh else "",
            "location_code": loc.full_code if loc else ""
        })
    return result


def get_inventory_items(db: Session, material_id: int, status: str = None, search: str = None):
    query = db.query(InventoryItem).filter(InventoryItem.material_id == material_id)
    if status:
        query = query.filter(InventoryItem.status == status)
    if search:
        query = query.filter(InventoryItem.code.contains(search))
    items = query.all()
    result = []
    for item in items:
        wh = db.query(Warehouse).filter(Warehouse.id == item.warehouse_id).first()
        loc = db.query(StorageLocation).filter(StorageLocation.id == item.location_id).first() if item.location_id else None
        result.append({
            "id": item.id, "material_id": item.material_id, "code": item.code,
            "status": item.status, "borrowed_by": item.borrowed_by,
            "borrow_time": item.borrow_time, "warehouse_id": item.warehouse_id,
            "location_id": item.location_id,
            "warehouse_name": wh.name if wh else "",
            "location_code": loc.full_code if loc else ""
        })
    return result


def borrow_material(db: Session, material_id: int, quantity: int, borrower: str,
                    item_code: str = None, warehouse_id: int = None, commit: bool = True,
                    reservation_application_id: int = None, actor_id: int = None,
                    record_transaction: bool = True):
    now = utcnow_iso()
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return {"ok": False, "msg": "物资不存在"}

    if m.has_individual_tracking:
        if not item_code:
            return {"ok": False, "msg": "请选择遥控器代号"}
        item = db.query(InventoryItem).filter(
            InventoryItem.material_id == material_id,
            InventoryItem.code == item_code
        ).with_for_update().first()
        if not item:
            return {"ok": False, "msg": f"遥控器 {item_code} 不存在"}
        if item.status != "available":
            if item.status == "borrowed":
                return {"ok": False, "msg": f"遥控器 {item_code} 已被借出"}
            if item.status == "missing":
                return {"ok": False, "msg": f"遥控器 {item_code} 盘点缺失，找回并确认入库后才能借出"}
            return {"ok": False, "msg": f"遥控器 {item_code} 当前状态不可借出"}
        from models import InventoryReservation
        reservation_query = db.query(InventoryReservation).filter(
            InventoryReservation.material_id == material_id,
            InventoryReservation.item_code == item_code,
            InventoryReservation.active.is_(True),
            InventoryReservation.expires_at > utcnow(),
        )
        if reservation_application_id is not None:
            reservation_query = reservation_query.filter(
                InventoryReservation.application_id != reservation_application_id
            )
        if reservation_query.first():
            return {"ok": False, "msg": f"遥控器 {item_code} 已被其他申请预留"}
        if not borrower.strip():
            return {"ok": False, "msg": "请输入借用人姓名"}
        item.status = "borrowed"
        item.borrowed_by = borrower.strip()
        item.borrow_time = now
        db.add(BorrowHistory(material_id=material_id, action="borrow", quantity=1,
                             borrower=borrower.strip(), item_code=item_code,
                             warehouse_id=item.warehouse_id, created_at=now))
        if record_transaction:
            db.add(InventoryTransaction(
                material_id=material_id, warehouse_id=item.warehouse_id, actor_id=actor_id,
                action="borrow", quantity=1, item_code=item_code,
            ))
        db.commit() if commit else db.flush()
        return {"ok": True, "msg": f"成功借出遥控器 {item_code}"}
    else:
        # Bulk material borrow
        from models import InventoryReservation
        total_available = get_material_inventory_summary(db, material_id)["total_quantity"]
        reservation_query = db.query(func.sum(InventoryReservation.quantity)).filter(
            InventoryReservation.material_id == material_id,
            InventoryReservation.active.is_(True),
            InventoryReservation.expires_at > utcnow(),
        )
        if reservation_application_id is not None:
            reservation_query = reservation_query.filter(
                InventoryReservation.application_id != reservation_application_id
            )
        total_available -= reservation_query.scalar() or 0
        if quantity > total_available:
            return {"ok": False, "msg": f"库存不足，仅剩 {total_available} 个"}
        if quantity <= 0:
            return {"ok": False, "msg": "借用数量必须大于0"}
        if not borrower.strip():
            return {"ok": False, "msg": "请输入借用人姓名"}

        # Deduct from batches with recycling-priority logic
        batches_query = db.query(InventoryBatch).filter(
            InventoryBatch.material_id == material_id,
            InventoryBatch.quantity > 0
        ).with_for_update()

        # Order batches by warehouse priority:
        # - recyclable items: recycling warehouse first, then main warehouse
        # - direct_consumption / new_consumable: main warehouse first
        if m.sub_category == "recyclable":
            # Find recycling warehouse
            recycling_wh = db.query(Warehouse).filter(Warehouse.name == "回收仓").first()
            if recycling_wh:
                # Recycling warehouse batches first, then others
                recycling_batches = batches_query.filter(
                    InventoryBatch.warehouse_id == recycling_wh.id
                ).order_by(InventoryBatch.id).all()
                other_batches = batches_query.filter(
                    InventoryBatch.warehouse_id != recycling_wh.id
                ).order_by(InventoryBatch.id).all()
                batches = recycling_batches + other_batches
            else:
                batches = batches_query.order_by(InventoryBatch.id).all()
        else:
            # Direct consumption or new consumable: prefer main warehouse
            main_wh = db.query(Warehouse).filter(Warehouse.name == "主仓库").first()
            if main_wh:
                main_batches = batches_query.filter(
                    InventoryBatch.warehouse_id == main_wh.id
                ).order_by(InventoryBatch.id).all()
                other_batches = batches_query.filter(
                    InventoryBatch.warehouse_id != main_wh.id
                ).order_by(InventoryBatch.id).all()
                batches = main_batches + other_batches
            else:
                batches = batches_query.order_by(InventoryBatch.id).all()

        remaining = quantity
        used_warehouse_id = None
        for batch in batches:
            if remaining <= 0:
                break
            deduct = min(batch.quantity, remaining)
            batch.quantity -= deduct
            batch.updated_at = now
            remaining -= deduct
            if used_warehouse_id is None:
                used_warehouse_id = batch.warehouse_id

        db.add(BorrowHistory(material_id=material_id, action="borrow", quantity=quantity,
                             borrower=borrower.strip(),
                             warehouse_id=warehouse_id or used_warehouse_id,
                             created_at=now))
        if record_transaction:
            db.add(InventoryTransaction(
                material_id=material_id, warehouse_id=warehouse_id or used_warehouse_id,
                actor_id=actor_id, action="borrow", quantity=quantity,
            ))
        db.commit() if commit else db.flush()
        return {"ok": True, "msg": f"成功借出 {quantity} 个{m.name}"}


def return_material(db: Session, material_id: int, quantity: int, returned_by: str,
                    item_code: str = None, warehouse_id: int = None, commit: bool = True,
                    actor_id: int = None, record_transaction: bool = True):
    now = utcnow_iso()
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return {"ok": False, "msg": "物资不存在"}

    if m.has_individual_tracking:
        if not item_code:
            return {"ok": False, "msg": "请选择遥控器代号"}
        item = db.query(InventoryItem).filter(
            InventoryItem.material_id == material_id,
            InventoryItem.code == item_code
        ).with_for_update().first()
        if not item:
            return {"ok": False, "msg": f"遥控器 {item_code} 不存在"}
        if item.status == "available":
            return {"ok": False, "msg": f"遥控器 {item_code} 未被借出"}
        if not returned_by.strip():
            return {"ok": False, "msg": "请输入归还人姓名"}
        item.status = "available"
        item.borrowed_by = None
        item.borrow_time = None
        db.add(BorrowHistory(material_id=material_id, action="return", quantity=1,
                             returned_by=returned_by.strip(), item_code=item_code,
                             warehouse_id=item.warehouse_id, created_at=now))
        if record_transaction:
            db.add(InventoryTransaction(
                material_id=material_id, warehouse_id=item.warehouse_id, actor_id=actor_id,
                action="return", quantity=1, item_code=item_code,
            ))
        db.commit() if commit else db.flush()
        return {"ok": True, "msg": f"成功归还遥控器 {item_code}"}
    else:
        total_borrowed = get_material_inventory_summary(db, material_id)["borrowed_quantity"]
        if quantity > total_borrowed:
            return {"ok": False, "msg": "归还数量超过已借出数量"}
        if quantity <= 0:
            return {"ok": False, "msg": "归还数量必须大于0"}

        # Return to the first batch of the specified warehouse, or create new batch
        target_warehouse_id = warehouse_id
        if not target_warehouse_id:
            first_batch = db.query(InventoryBatch).filter(
                InventoryBatch.material_id == material_id
            ).first()
            target_warehouse_id = first_batch.warehouse_id if first_batch else None

        if target_warehouse_id:
            batch = db.query(InventoryBatch).filter(
                InventoryBatch.material_id == material_id,
                InventoryBatch.warehouse_id == target_warehouse_id
            ).first()
            if batch:
                batch.quantity += quantity
                batch.updated_at = now
            else:
                db.add(InventoryBatch(material_id=material_id, warehouse_id=target_warehouse_id,
                                      quantity=quantity, created_at=now, updated_at=now))
        else:
            # No warehouse assigned yet — create a default batch
            wh = db.query(Warehouse).first()
            if wh:
                db.add(InventoryBatch(material_id=material_id, warehouse_id=wh.id,
                                      quantity=quantity, created_at=now, updated_at=now))

        db.add(BorrowHistory(material_id=material_id, action="return", quantity=quantity,
                             returned_by=returned_by.strip(), warehouse_id=target_warehouse_id, created_at=now))
        if record_transaction:
            db.add(InventoryTransaction(
                material_id=material_id, warehouse_id=target_warehouse_id, actor_id=actor_id,
                action="return", quantity=quantity,
            ))
        db.commit() if commit else db.flush()
        return {"ok": True, "msg": f"成功归还 {quantity} 个{m.name}"}
