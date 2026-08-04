from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import WarehouseCreate, LocationCreate, LocationUpdate, ApiResponse

router = APIRouter()


@router.get("/warehouses")
def list_warehouses(db: Session = Depends(get_db)):
    from models import Warehouse
    warehouses = db.query(Warehouse).all()
    data = [{"id": w.id, "name": w.name, "location_desc": w.location_desc} for w in warehouses]
    return {"ok": True, "data": data, "msg": ""}


@router.post("/warehouses")
def create_warehouse(body: WarehouseCreate, db: Session = Depends(get_db)):
    from models import Warehouse
    w = Warehouse(name=body.name, location_desc=body.location_desc)
    db.add(w)
    db.commit()
    db.refresh(w)
    return {"ok": True, "data": {"id": w.id, "name": w.name}, "msg": "仓库创建成功"}


@router.get("/warehouses/{warehouse_id}/locations")
def list_locations(warehouse_id: int, db: Session = Depends(get_db)):
    from models import StorageLocation
    locs = db.query(StorageLocation).filter(StorageLocation.warehouse_id == warehouse_id).all()
    data = [{"id": l.id, "warehouse_id": l.warehouse_id, "shelf": l.shelf,
             "level": l.level, "position": l.position, "full_code": l.full_code} for l in locs]
    return {"ok": True, "data": data, "msg": ""}


@router.get("/locations")
def list_all_locations(db: Session = Depends(get_db)):
    from models import StorageLocation, Warehouse
    locs = db.query(StorageLocation).all()
    data = []
    for l in locs:
        wh = db.query(Warehouse).filter(Warehouse.id == l.warehouse_id).first()
        data.append({
            "id": l.id, "warehouse_id": l.warehouse_id,
            "shelf": l.shelf, "level": l.level, "position": l.position,
            "full_code": l.full_code, "warehouse_name": wh.name if wh else ""
        })
    return {"ok": True, "data": data, "msg": ""}


@router.get("/locations/search")
def search_locations(q: str = "", db: Session = Depends(get_db)):
    from models import StorageLocation, Warehouse
    query = db.query(StorageLocation)
    if q:
        query = query.filter(StorageLocation.full_code.contains(q))
    locs = query.all()
    data = []
    for l in locs:
        wh = db.query(Warehouse).filter(Warehouse.id == l.warehouse_id).first()
        data.append({
            "id": l.id, "warehouse_id": l.warehouse_id,
            "shelf": l.shelf, "level": l.level, "position": l.position,
            "full_code": l.full_code, "warehouse_name": wh.name if wh else ""
        })
    return {"ok": True, "data": data, "msg": ""}


@router.post("/locations")
def create_location(body: LocationCreate, db: Session = Depends(get_db)):
    from models import StorageLocation, Warehouse
    wh = db.query(Warehouse).filter(Warehouse.id == body.warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="仓库不存在")
    full_code = f"{body.shelf}-{body.level}-{body.position}" if body.position else f"{body.shelf}-{body.level}"
    existing = db.query(StorageLocation).filter(
        StorageLocation.warehouse_id == body.warehouse_id,
        StorageLocation.full_code == full_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"储位 {full_code} 已存在")
    l = StorageLocation(warehouse_id=body.warehouse_id, shelf=body.shelf,
                        level=body.level, position=body.position, full_code=full_code)
    db.add(l)
    db.commit()
    db.refresh(l)
    return {"ok": True, "data": {"id": l.id, "full_code": l.full_code}, "msg": "储位创建成功"}


@router.put("/locations/{location_id}")
def update_location(location_id: int, body: LocationUpdate, db: Session = Depends(get_db)):
    from models import StorageLocation
    l = db.query(StorageLocation).filter(StorageLocation.id == location_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="储位不存在")
    if body.shelf is not None:
        l.shelf = body.shelf
    if body.level is not None:
        l.level = body.level
    if body.position is not None:
        l.position = body.position
    l.full_code = f"{l.shelf}-{l.level}-{l.position}" if l.position else f"{l.shelf}-{l.level}"
    db.commit()
    return {"ok": True, "data": None, "msg": "储位更新成功"}


@router.delete("/locations/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    from models import StorageLocation, InventoryItem, InventoryBatch
    l = db.query(StorageLocation).filter(StorageLocation.id == location_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="储位不存在")
    has_items = db.query(InventoryItem).filter(InventoryItem.location_id == location_id).count() > 0
    has_batches = db.query(InventoryBatch).filter(InventoryBatch.location_id == location_id).count() > 0
    if has_items or has_batches:
        raise HTTPException(status_code=400, detail="该储位仍有库存，无法删除")
    db.delete(l)
    db.commit()
    return {"ok": True, "data": None, "msg": "储位已删除"}


@router.get("/warehouses/stats")
def warehouse_stats(db: Session = Depends(get_db)):
    from models import Warehouse, InventoryBatch, InventoryItem, Material
    from sqlalchemy import func

    warehouses = db.query(Warehouse).all()
    data = []
    for w in warehouses:
        # Count materials that have inventory in this warehouse
        batch_material_ids = set(
            r[0] for r in db.query(InventoryBatch.material_id).filter(
                InventoryBatch.warehouse_id == w.id,
                InventoryBatch.quantity > 0
            ).all()
        )
        item_material_ids = set(
            r[0] for r in db.query(InventoryItem.material_id).filter(
                InventoryItem.warehouse_id == w.id
            ).all()
        )
        material_ids = batch_material_ids | item_material_ids

        # Total quantity
        batch_qty = db.query(func.sum(InventoryBatch.quantity)).filter(
            InventoryBatch.warehouse_id == w.id
        ).scalar() or 0
        item_qty = db.query(InventoryItem).filter(
            InventoryItem.warehouse_id == w.id
        ).count()
        total_qty = batch_qty + item_qty

        # Low stock count
        low_stock = 0
        for mid in material_ids:
            m = db.query(Material).filter(Material.id == mid).first()
            if not m:
                continue
            if m.has_individual_tracking:
                available = db.query(InventoryItem).filter(
                    InventoryItem.material_id == mid,
                    InventoryItem.warehouse_id == w.id,
                    InventoryItem.status == "available"
                ).count()
            else:
                available = db.query(func.sum(InventoryBatch.quantity)).filter(
                    InventoryBatch.material_id == mid,
                    InventoryBatch.warehouse_id == w.id
                ).scalar() or 0
            if available <= m.low_stock_threshold:
                low_stock += 1

        data.append({
            "id": w.id,
            "name": w.name,
            "location_desc": w.location_desc,
            "materials_count": len(material_ids),
            "total_quantity": total_qty,
            "low_stock_count": low_stock,
        })

    return {"ok": True, "data": data, "msg": ""}


@router.get("/warehouses/{warehouse_id}/detail")
def warehouse_detail(warehouse_id: int, db: Session = Depends(get_db)):
    from models import Warehouse, StorageLocation, Material, InventoryBatch, InventoryItem
    from sqlalchemy import func

    w = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="仓库不存在")

    # Locations
    locs = db.query(StorageLocation).filter(
        StorageLocation.warehouse_id == warehouse_id
    ).all()
    locations_data = [{
        "id": l.id, "shelf": l.shelf, "level": l.level,
        "position": l.position, "full_code": l.full_code
    } for l in locs]

    # Materials in this warehouse
    materials_data = []
    # From batches
    batches = db.query(InventoryBatch).filter(
        InventoryBatch.warehouse_id == warehouse_id,
        InventoryBatch.quantity > 0
    ).all()
    seen_material_ids = set()
    for b in batches:
        m = db.query(Material).filter(Material.id == b.material_id).first()
        if not m or m.id in seen_material_ids:
            continue
        seen_material_ids.add(m.id)
        loc = db.query(StorageLocation).filter(
            StorageLocation.id == b.location_id
        ).first() if b.location_id else None
        materials_data.append({
            "id": m.id, "name": m.name, "spec": m.spec, "unit": m.unit,
            "icon": m.icon, "color_idx": m.color_idx,
            "category": m.category, "sub_category": m.sub_category,
            "has_individual_tracking": bool(m.has_individual_tracking),
            "low_stock_threshold": m.low_stock_threshold,
            "total_quantity": b.quantity,
            "location_code": loc.full_code if loc else "",
            "location_id": b.location_id,
        })

    # From individual items
    items = db.query(InventoryItem).filter(
        InventoryItem.warehouse_id == warehouse_id
    ).all()
    for item in items:
        if item.material_id in seen_material_ids:
            continue
        seen_material_ids.add(item.material_id)
        m = db.query(Material).filter(Material.id == item.material_id).first()
        if not m:
            continue
        total = db.query(InventoryItem).filter(
            InventoryItem.material_id == m.id,
            InventoryItem.warehouse_id == warehouse_id
        ).count()
        loc = db.query(StorageLocation).filter(
            StorageLocation.id == item.location_id
        ).first() if item.location_id else None
        materials_data.append({
            "id": m.id, "name": m.name, "spec": m.spec, "unit": m.unit,
            "icon": m.icon, "color_idx": m.color_idx,
            "category": m.category, "sub_category": m.sub_category,
            "has_individual_tracking": bool(m.has_individual_tracking),
            "low_stock_threshold": m.low_stock_threshold,
            "total_quantity": total,
            "location_code": loc.full_code if loc else "",
            "location_id": item.location_id,
        })

    return {"ok": True, "data": {
        "id": w.id, "name": w.name, "location_desc": w.location_desc,
        "materials": materials_data, "locations": locations_data,
    }, "msg": ""}