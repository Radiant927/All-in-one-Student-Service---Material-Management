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