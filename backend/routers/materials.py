from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from schemas import MaterialCreate, MaterialUpdate, MaterialOut, ApiResponse

router = APIRouter()


@router.get("/materials")
def list_materials(
    category: Optional[str] = None,
    search: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    from models import Material
    from services.inventory_service import get_material_inventory_summary

    query = db.query(Material)
    if category:
        query = query.filter(Material.category == category)
    if search:
        q = f"%{search}%"
        query = query.filter(Material.name.like(q))
    materials = query.all()

    result = []
    for m in materials:
        d = m.__dict__.copy()
        summary = get_material_inventory_summary(db, m.id)
        d["total_quantity"] = summary["total_quantity"]
        d["borrowed_quantity"] = summary["borrowed_quantity"]
        d["available_quantity"] = summary["available_quantity"]
        d["has_individual_tracking"] = bool(m.has_individual_tracking)
        result.append(d)

    if warehouse_id:
        result = [r for r in result if r["total_quantity"] > 0]

    return {"ok": True, "data": result, "msg": ""}


@router.get("/materials/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db)):
    from models import Material
    from services.inventory_service import get_material_inventory_summary

    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物资不存在")

    d = m.__dict__.copy()
    summary = get_material_inventory_summary(db, m.id)
    d["total_quantity"] = summary["total_quantity"]
    d["borrowed_quantity"] = summary["borrowed_quantity"]
    d["available_quantity"] = summary["available_quantity"]
    d["has_individual_tracking"] = bool(m.has_individual_tracking)
    return {"ok": True, "data": d, "msg": ""}


@router.post("/materials")
def create_material(body: MaterialCreate, db: Session = Depends(get_db)):
    from models import Material
    from datetime import datetime

    now = datetime.now().isoformat()
    m = Material(
        name=body.name,
        spec=body.spec,
        unit=body.unit,
        category=body.category,
        sub_category=body.sub_category,
        has_individual_tracking=1 if body.has_individual_tracking else 0,
        low_stock_threshold=body.low_stock_threshold,
        icon=body.icon,
        color_idx=body.color_idx,
        created_at=now,
        updated_at=now,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"ok": True, "data": {"id": m.id, "name": m.name}, "msg": "物资创建成功"}


@router.put("/materials/{material_id}")
def update_material(material_id: int, body: MaterialUpdate, db: Session = Depends(get_db)):
    from models import Material
    from datetime import datetime

    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物资不存在")

    update_data = body.model_dump(exclude_unset=True)
    if "has_individual_tracking" in update_data:
        update_data["has_individual_tracking"] = 1 if update_data["has_individual_tracking"] else 0
    update_data["updated_at"] = datetime.now().isoformat()

    for k, v in update_data.items():
        setattr(m, k, v)
    db.commit()
    return {"ok": True, "data": None, "msg": "物资更新成功"}


@router.delete("/materials/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    from models import Material, InventoryItem, InventoryBatch

    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物资不存在")

    has_inventory = db.query(InventoryItem).filter(InventoryItem.material_id == material_id).count() > 0
    has_batches = db.query(InventoryBatch).filter(InventoryBatch.material_id == material_id).count() > 0
    if has_inventory or has_batches:
        raise HTTPException(status_code=400, detail="该物资仍有库存记录，无法删除")

    db.delete(m)
    db.commit()
    return {"ok": True, "data": None, "msg": "物资已删除"}


@router.get("/materials/{material_id}/warehouse-breakdown")
def material_warehouse_breakdown(material_id: int, db: Session = Depends(get_db)):
    from models import Material, InventoryBatch, InventoryItem, Warehouse, StorageLocation
    from sqlalchemy import func

    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="物资不存在")

    breakdown = []
    warehouses = db.query(Warehouse).all()

    for wh in warehouses:
        qty = 0
        location_code = ""

        if m.has_individual_tracking:
            qty = db.query(InventoryItem).filter(
                InventoryItem.material_id == material_id,
                InventoryItem.warehouse_id == wh.id
            ).count()
        else:
            batches = db.query(InventoryBatch).filter(
                InventoryBatch.material_id == material_id,
                InventoryBatch.warehouse_id == wh.id,
                InventoryBatch.quantity > 0
            ).all()
            qty = sum(b.quantity for b in batches)
            if batches and batches[0].location_id:
                loc = db.query(StorageLocation).filter(
                    StorageLocation.id == batches[0].location_id
                ).first()
                if loc:
                    location_code = loc.full_code

        if qty > 0:
            breakdown.append({
                "warehouse_id": wh.id,
                "warehouse_name": wh.name,
                "quantity": qty,
                "location_code": location_code,
            })

    return {"ok": True, "data": breakdown, "msg": ""}