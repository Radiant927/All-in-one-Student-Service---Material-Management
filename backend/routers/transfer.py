from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import TransferRequest
from constants import UserRole
from models import User
from security import require_roles

router = APIRouter()


@router.post("/transfer")
def transfer_material(
    body: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR.value, UserRole.ADMIN.value)),
):
    from models import Material, Warehouse, InventoryBatch, InventoryItem, BorrowHistory, InventoryTransaction
    from datetime import datetime

    if body.from_warehouse_id == body.to_warehouse_id:
        return {"ok": False, "data": None, "msg": "调出和调入仓库不能相同"}

    # Validate material exists
    m = db.query(Material).filter(Material.id == body.material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物资不存在")

    # Validate warehouses exist
    from_wh = db.query(Warehouse).filter(Warehouse.id == body.from_warehouse_id).first()
    to_wh = db.query(Warehouse).filter(Warehouse.id == body.to_warehouse_id).first()
    if not from_wh:
        raise HTTPException(status_code=404, detail="调出仓库不存在")
    if not to_wh:
        raise HTTPException(status_code=404, detail="调入仓库不存在")

    now = datetime.now().isoformat()

    if m.has_individual_tracking:
        # Transfer individual items
        items = db.query(InventoryItem).filter(
            InventoryItem.material_id == body.material_id,
            InventoryItem.warehouse_id == body.from_warehouse_id,
            InventoryItem.status == "available"
        ).with_for_update().limit(body.quantity).all()

        if len(items) < body.quantity:
            return {"ok": False, "data": None,
                    "msg": f"调出仓库可用个体不足，仅有 {len(items)} 个"}

        for item in items:
            item.warehouse_id = body.to_warehouse_id
            item.location_id = body.location_id

        db.add(BorrowHistory(
            material_id=body.material_id,
            action="transfer",
            quantity=body.quantity,
            borrower=from_wh.name,
            returned_by=to_wh.name,
            warehouse_id=body.to_warehouse_id,
            created_at=now
        ))
        db.add(InventoryTransaction(
            material_id=body.material_id,
            warehouse_id=body.to_warehouse_id,
            actor_id=current_user.id,
            action="transfer",
            quantity=body.quantity,
        ))
        db.commit()
        return {"ok": True, "data": None,
                "msg": f"成功调拨 {body.quantity} 个 {m.name} 从 {from_wh.name} 到 {to_wh.name}"}

    else:
        # Transfer batch quantities
        batches = db.query(InventoryBatch).filter(
            InventoryBatch.material_id == body.material_id,
            InventoryBatch.warehouse_id == body.from_warehouse_id,
            InventoryBatch.quantity > 0
        ).order_by(InventoryBatch.id).with_for_update().all()

        total_available = sum(b.quantity for b in batches)
        if total_available < body.quantity:
            return {"ok": False, "data": None,
                    "msg": f"调出仓库库存不足，仅有 {total_available} 个"}

        remaining = body.quantity
        for batch in batches:
            if remaining <= 0:
                break
            deduct = min(batch.quantity, remaining)
            batch.quantity -= deduct
            batch.updated_at = now
            remaining -= deduct

        # Clean up empty batches
        for batch in batches:
            if batch.quantity <= 0:
                db.delete(batch)

        # Create or update batch in target warehouse
        target_batch = db.query(InventoryBatch).filter(
            InventoryBatch.material_id == body.material_id,
            InventoryBatch.warehouse_id == body.to_warehouse_id,
            InventoryBatch.location_id == body.location_id
        ).first()

        if target_batch:
            target_batch.quantity += body.quantity
            target_batch.updated_at = now
        else:
            target_batch = InventoryBatch(
                material_id=body.material_id,
                warehouse_id=body.to_warehouse_id,
                location_id=body.location_id,
                quantity=body.quantity,
                created_at=now,
                updated_at=now
            )
            db.add(target_batch)

        db.add(BorrowHistory(
            material_id=body.material_id,
            action="transfer",
            quantity=body.quantity,
            borrower=from_wh.name,
            returned_by=to_wh.name,
            warehouse_id=body.to_warehouse_id,
            created_at=now
        ))
        db.add(InventoryTransaction(
            material_id=body.material_id,
            warehouse_id=body.to_warehouse_id,
            actor_id=current_user.id,
            action="transfer",
            quantity=body.quantity,
        ))
        db.commit()
        return {"ok": True, "data": None,
                "msg": f"成功调拨 {body.quantity} 个 {m.name} 从 {from_wh.name} 到 {to_wh.name}"}
