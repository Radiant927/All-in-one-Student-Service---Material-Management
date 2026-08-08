from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from constants import UserRole
from models import User
from security import require_roles
from schemas import InventoryItemCreate, InventoryBatchCreate, InventoryBatchUpdate, InboundRequest, ApiResponse
from services.inventory_service import get_material_inventory_summary, get_inventory_items, get_inventory_batches

router = APIRouter()


@router.get("/inventory/summary/{material_id}")
def inventory_summary(material_id: int, db: Session = Depends(get_db)):
    summary = get_material_inventory_summary(db, material_id)
    batches = get_inventory_batches(db, material_id)
    return {"ok": True, "data": {**summary, "batches": batches}, "msg": ""}


@router.get("/inventory/items/{material_id}")
def list_inventory_items(
    material_id: int,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    items = get_inventory_items(db, material_id, status=status, search=search)
    return {"ok": True, "data": items, "msg": ""}


@router.post("/inventory/items")
def add_inventory_items(body: InventoryItemCreate, db: Session = Depends(get_db)):
    from models import Material, InventoryItem, Warehouse
    from datetime import datetime

    m = db.query(Material).filter(Material.id == body.material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物资不存在")
    if not m.has_individual_tracking:
        raise HTTPException(status_code=400, detail="该物资不支持个体追踪")

    wh = db.query(Warehouse).filter(Warehouse.id == body.warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="仓库不存在")

    now = datetime.now().isoformat()
    pad_len = max(3, len(str(body.start_num + body.count - 1)))
    added = []
    for i in range(body.count):
        num = str(body.start_num + i).zfill(pad_len)
        code = f"{body.prefix}-{num}"
        if db.query(InventoryItem).filter(InventoryItem.code == code).first():
            raise HTTPException(status_code=400, detail=f"代号 {code} 已存在")
        item = InventoryItem(material_id=body.material_id, code=code, status="available",
                             warehouse_id=body.warehouse_id, location_id=body.location_id,
                             created_at=now)
        db.add(item)
        added.append(code)

    db.commit()
    return {"ok": True, "data": {"added": added, "count": len(added)},
            "msg": f"成功添加 {len(added)} 个个体"}


@router.delete("/inventory/items/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    from models import InventoryItem
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个体不存在")
    if item.status == "borrowed":
        raise HTTPException(status_code=400, detail="该个体已被借出，请先归还再删除")
    db.delete(item)
    db.commit()
    return {"ok": True, "data": None, "msg": f"已删除 {item.code}"}


@router.post("/inventory/batches")
def create_inventory_batch(body: InventoryBatchCreate, db: Session = Depends(get_db)):
    from models import Material, InventoryBatch, Warehouse
    from datetime import datetime

    m = db.query(Material).filter(Material.id == body.material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物资不存在")
    if m.has_individual_tracking:
        raise HTTPException(status_code=400, detail="个体追踪物资请使用 /inventory/items 接口")

    now = datetime.now().isoformat()
    existing = db.query(InventoryBatch).filter(
        InventoryBatch.material_id == body.material_id,
        InventoryBatch.warehouse_id == body.warehouse_id,
        InventoryBatch.location_id == body.location_id
    ).first()
    if existing:
        existing.quantity = body.quantity
        existing.updated_at = now
    else:
        existing = InventoryBatch(material_id=body.material_id, warehouse_id=body.warehouse_id,
                                  location_id=body.location_id, quantity=body.quantity,
                                  created_at=now, updated_at=now)
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return {"ok": True, "data": {"id": existing.id, "quantity": existing.quantity}, "msg": "库存更新成功"}


@router.put("/inventory/batches/{batch_id}")
def update_inventory_batch(batch_id: int, body: InventoryBatchUpdate, db: Session = Depends(get_db)):
    from models import InventoryBatch
    from datetime import datetime

    batch = db.query(InventoryBatch).filter(InventoryBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="库存批次不存在")
    batch.quantity = body.quantity
    batch.updated_at = datetime.now().isoformat()
    db.commit()
    return {"ok": True, "data": None, "msg": "库存更新成功"}


@router.post("/inbound")
def inbound_material(
    body: InboundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR.value, UserRole.ADMIN.value)),
):
    from models import Material, Warehouse, InventoryBatch, BorrowHistory, InventoryTransaction
    from datetime import datetime

    m = db.query(Material).filter(Material.id == body.material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物资不存在")
    if m.has_individual_tracking:
        raise HTTPException(status_code=400, detail="个体追踪物资请使用 /inventory/items 接口添加入库")

    wh = db.query(Warehouse).filter(Warehouse.id == body.warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="仓库不存在")

    if body.quantity <= 0:
        return {"ok": False, "data": None, "msg": "入库数量必须大于0"}

    now = datetime.now().isoformat()

    # Upsert batch
    existing = db.query(InventoryBatch).filter(
        InventoryBatch.material_id == body.material_id,
        InventoryBatch.warehouse_id == body.warehouse_id,
        InventoryBatch.location_id == body.location_id
    ).with_for_update().first()

    if existing:
        existing.quantity += body.quantity
        existing.updated_at = now
        new_qty = existing.quantity
    else:
        existing = InventoryBatch(
            material_id=body.material_id, warehouse_id=body.warehouse_id,
            location_id=body.location_id, quantity=body.quantity,
            created_at=now, updated_at=now
        )
        db.add(existing)
        new_qty = body.quantity

    # Record inbound history
    db.add(BorrowHistory(
        material_id=body.material_id,
        action="inbound",
        quantity=body.quantity,
        borrower="入库操作",
        warehouse_id=body.warehouse_id,
        created_at=now
    ))
    db.add(InventoryTransaction(
        material_id=body.material_id,
        warehouse_id=body.warehouse_id,
        actor_id=current_user.id,
        action="inbound",
        quantity=body.quantity,
    ))

    db.commit()
    loc_desc = ""
    if body.location_id:
        from models import StorageLocation
        loc = db.query(StorageLocation).filter(StorageLocation.id == body.location_id).first()
        if loc:
            loc_desc = f" → {loc.full_code}"

    return {"ok": True,
            "data": {"batch_id": existing.id, "quantity": new_qty, "warehouse_name": wh.name},
            "msg": f"成功入库 {body.quantity} 个 {m.name} 到 {wh.name}{loc_desc}"}
